// Derived from refineR 2.0.0, calculateCostHist and getSumForPArea by
// Tatjana Ammer, the Box-Cox helpers by Andre Schuetzenmeister, and the
// normal CDF lookup by Christopher M Rank.
// Upstream authors: Matthias Beck, Tatjana Ammer, Christopher M Rank and
// Andre Schuetzenmeister. Upstream license GPL (>= 3); this derivative GPL-3.
// Preserve the evaluation order of the upstream formulas. Each output row
// profiles P and rf at one supplied (lambda, mu, sigma), so an anchor score
// for that theta can be added before any shape parameter is selected.
#define R_NO_REMAP
#include <R.h>
#include <Rinternals.h>
#include <Rmath.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <climits>
#include <cstring>
#include <limits>
#include <stdexcept>
#include <vector>

namespace {
using Values = std::vector<double>;
constexpr double infinity = std::numeric_limits<double>::infinity();
constexpr int area_count = 11;

SEXP field(SEXP list, const char* key) {
    if (TYPEOF(list) != VECSXP) throw std::invalid_argument("expected a named R list");
    SEXP names = Rf_getAttrib(list, R_NamesSymbol);
    if (TYPEOF(names) == STRSXP) {
        for (R_xlen_t i = 0; i < XLENGTH(names); ++i)
            if (!std::strcmp(CHAR(STRING_ELT(names, i)), key)) return VECTOR_ELT(list, i);
    }
    throw std::invalid_argument(key);
}

Values numbers(SEXP x) {
    if (TYPEOF(x) == REALSXP) return Values(REAL(x), REAL(x) + XLENGTH(x));
    if (TYPEOF(x) == INTSXP) {
        Values result(XLENGTH(x));
        for (R_xlen_t i = 0; i < XLENGTH(x); ++i)
            result[i] = INTEGER(x)[i] == NA_INTEGER ? NA_REAL : static_cast<double>(INTEGER(x)[i]);
        return result;
    }
    throw std::invalid_argument("expected numeric vector");
}

double transform(double x, double lambda) {
    return std::abs(lambda) < 1e-20 ? std::log(x) : (R_pow(x, lambda) - 1.0) / lambda;
}

struct Histogram {
    Values obs, left, right, transformed_left, transformed_right, lookup;
    std::vector<int> fine_left, fine_right;
    Values cumulative;
    double lambda, inv_step, n_data, nominal, min_edge, max_edge;
    const double z = -Rf_qnorm5(0.01 / 2.0, 0.0, 1.0, 1, 0);
    int bins, max_below;

    Histogram(double power, SEXP hist, SEXP table)
        : obs(numbers(field(hist, "counts"))), left(numbers(field(hist, "breakL"))),
          right(numbers(field(hist, "breakR"))), lookup(numbers(field(table, "val"))),
          lambda(power), inv_step(1.0 / Rf_asReal(field(table, "h"))),
          n_data(Rf_asReal(field(hist, "NData"))),
          nominal(Rf_asReal(field(hist, "NBins")) * Rf_asReal(field(hist, "overlapFactor"))),
          bins(static_cast<int>(obs.size())), max_below(std::ceil(bins * 0.1 / 2.0)) {
        SEXP full = field(hist, "fullHist");
        Values breaks = numbers(field(full, "breaks")), counts = numbers(field(full, "counts"));
        if (bins < 3 || left.size() != obs.size() || right.size() != obs.size() ||
            breaks.size() != counts.size() + 1 || !std::is_sorted(breaks.begin(), breaks.end()) ||
            lookup.size() < 3 || !std::isfinite(inv_step) || inv_step <= 0)
            throw std::invalid_argument("invalid histogram or normal lookup");
        cumulative.push_back(0.0);
        for (double count : counts) cumulative.push_back(cumulative.back() + count);
        // The upper cut is exclusive in getSumForPArea. Duplicate border
        // breaks still select exactly the original integer fine-cell counts.
        auto prefix_index = [&](double edge) {
            return static_cast<int>(std::lower_bound(breaks.begin(), breaks.end() - 1, edge)
                                    - breaks.begin());
        };
        for (int i = 0; i < bins; ++i) {
            transformed_left.push_back(transform(left[i], power));
            transformed_right.push_back(transform(right[i], power));
            fine_left.push_back(prefix_index(left[i]));
            fine_right.push_back(prefix_index(right[i]));
        }
        min_edge = *std::min_element(transformed_left.begin(), transformed_left.end());
        max_edge = *std::max_element(transformed_right.begin(), transformed_right.end());
    }

    double approximate(double edge, double mu, double inv_sd) const {
        double index = ((edge - mu) * inv_sd + 5.2) * inv_step;
        if (index < 0) index = 0;
        if (index >= lookup.size() - 2.0) index = lookup.size() - 1.5;
        if (std::isnan(index)) return NA_REAL;
        const int i = static_cast<int>(index);
        const double w = index - i;
        return (1.0 - w) * lookup[i] + w * lookup[i + 1];
    }
};

struct Area {
    int left = -1, right = -1;
    void add(int j, const Histogram& h) {
        if (left == -1 || h.left[j] < h.left[left]) left = j;
        if (right == -1 || h.right[j] > h.right[right]) right = j;
    }
};

using Areas = std::array<double, area_count>;

// Implements the two 0.001-step ratio-adjustment loops. Disabled elements
// stop moving on a given iteration, just as with the R logical subscript.
double fraction_limit(const Areas& data, const Areas& pred, double z, bool upper) {
    Areas ratios;
    for (int i = 0; i < area_count; ++i) ratios[i] = data[i] / pred[i];
    while (true) {
        std::array<bool, area_count> move;
        int selected = 0;
        bool within = true;
        for (int i = 0; i < area_count; ++i) {
            if (upper ? ratios[i] > 1.0 : ratios[i] < 0.4) { within = false; break; }
            const double expected = ratios[i] * pred[i];
            const double width = z * std::sqrt(expected);
            move[i] = upper ? expected - width <= data[i] : expected + width >= data[i];
            selected += move[i];
        }
        if (!within || selected <= (upper ? 5 : 1)) break;
        for (int i = 0; i < area_count; ++i)
            if (move[i]) ratios[i] += upper ? 0.001 : -0.001;
    }
    const double limit = *std::min_element(ratios.begin(), ratios.end());
    return upper ? std::min(std::max(0.401, limit), 1.0)
                 : std::min(std::max(0.400, limit), 0.999);
}

double penalty(double ratio) {
    // min(1, ratio, na.rm=TRUE) returns 1 for the empty 0/0 ratio.
    double clamped = std::max(0.01, std::min(1.0, ratio));
    return clamped * clamped;
}

struct Profile {
    double p = NA_REAL, cost = infinity, rf = NA_REAL, k = NA_REAL;
};

struct Buffer {
    Values pred, root;
    std::vector<unsigned char> peak80, peak95;
    explicit Buffer(int bins) : pred(bins), root(bins), peak80(bins), peak95(bins) {}
};

Profile profile(const Histogram& h, double mu, double sigma, Buffer& work) {
    Profile best;
    if (!(sigma > 0) || !std::isfinite(mu) || !std::isfinite(sigma)) return best;
    const double y = mu - h.z * sigma;
    const double lower_ri = std::abs(h.lambda) < 1e-20 ? std::exp(y)
                         : R_pow(h.lambda * y + 1.0, 1.0 / h.lambda);
    if (std::isnan(lower_ri)) return best;
    const double corr = 1.0 / (Rf_pnorm5(h.max_edge, mu, sigma, 1, 0)
                              - Rf_pnorm5(h.min_edge, mu, sigma, 1, 0));
    if (!std::isfinite(corr)) return best;
    const double count_scale = corr * h.n_data;
    const double inv_sd = 1.0 / sigma;
    int adequate = 0;
    for (int i = 0; i < h.bins; ++i) {
        double count = count_scale * (h.approximate(h.transformed_right[i], mu, inv_sd)
                                    - h.approximate(h.transformed_left[i], mu, inv_sd));
        if (!std::isfinite(count)) return best;
        work.pred[i] = std::max(count, 0.0);
        work.root[i] = std::sqrt(work.pred[i]);
        adequate += work.pred[i] >= 20.0;
    }
    if (adequate <= h.nominal / 16.0) return best;

    // Upstream "2:length(countsPred)-1" takes indices 1 through B-1.
    // In contrast getSumForPArea finds its peak over all B entries.
    const double peak = *std::max_element(work.pred.begin(), work.pred.end() - 1);
    const int peak_index = std::find_if(work.pred.begin(), work.pred.end(),
        [&](double d) { return std::abs(d - peak) < 1e-20; }) - work.pred.begin();
    const int area_peak_index = std::max_element(work.pred.begin(), work.pred.end()) - work.pred.begin();
    const double area_peak = work.pred[area_peak_index];
    const double area_lo[] = {0.5, 0.55, 0.60, 0.65, 0.70};
    const double area_hi[] = {0.9, 0.94, 0.95, 0.96, 0.97};
    std::array<Area, area_count> areas;
    long double pred_l = 0, pred_r = 0;
    double data_l = 0, data_r = 0;
    int peak95_count = 0;
    for (int i = 0; i < h.bins; ++i) {
        const double c = work.pred[i];
        const bool middle = i != 0 && i != h.bins - 1;
        work.peak80[i] = middle && c >= 0.80 * peak;
        work.peak95[i] = middle && c >= 0.95 * peak;
        peak95_count += work.peak95[i];
        if (i == 0 || (i < peak_index && c <= 0.20 * peak)) {
            data_l += h.obs[i]; pred_l += c;
        }
        if (i == h.bins - 1 || (i > peak_index && c <= 0.20 * peak)) {
            data_r += h.obs[i]; pred_r += c;
        }
        if (c >= 0.95 * area_peak) areas[0].add(i, h);
        if (c < 0.5 * area_peak || c >= 0.97 * area_peak) continue;
        for (int j = 0; j < 5; ++j) {
            if (c >= area_lo[j] * area_peak && c < area_hi[j] * area_peak) {
                if (i <= area_peak_index) areas[2*j + 1].add(i, h);
                if (i >= area_peak_index) areas[2*j + 2].add(i, h);
            }
        }
    }

    Areas data_area, pred_area;
    for (int j = 0; j < area_count; ++j) {
        const Area& a = areas[j];
        if (a.left < 0) {
            data_area[j] = pred_area[j] = 1.0;
        } else {
            data_area[j] = h.cumulative[h.fine_right[a.right]] - h.cumulative[h.fine_left[a.left]];
            pred_area[j] = count_scale * (Rf_pnorm5(h.transformed_right[a.right], mu, sigma, 1, 0)
                                        - Rf_pnorm5(h.transformed_left[a.left], mu, sigma, 1, 0));
            if (std::abs(pred_area[j]) < 1e-20) pred_area[j] = 1.0;
        }
    }
    const double upper = fraction_limit(data_area, pred_area, h.z, true);
    const double lower = fraction_limit(data_area, pred_area, h.z, false);
    const double step = std::min(std::max(0.002, (upper - lower) / 8.0), 0.01);
    // seq.default uses floor((to-from)/by + 1e-10) and clamps at to,
    // then refineR appends PMax even when it is the preceding grid entry.
    const int last = static_cast<int>(std::floor((upper - lower) / step + 1e-10));
    const double tail_l = data_l / static_cast<double>(pred_l);
    const double tail_r = data_r / static_cast<double>(pred_r);
    for (int ip = 0; ip <= last + 1; ++ip) {
        const double p = ip == last + 1 ? upper : std::min(upper, lower + ip * step);
        const double tail_log_l = std::log(penalty(tail_l / p));
        const double tail_log_r = std::log(penalty(tail_r / p));
        bool advance = true;
        for (double gamma : {0.005, 0.003, 0.001, 0.0}) {
            double rf = 1.0;
            if (gamma != 0) {
                const double v = gamma * p * peak + std::sqrt(p * peak);
                rf = p * peak / (v * v);
                if (!(rf > 0.001 && rf < 1)) continue;
            }
            const double sqrt_pr = std::sqrt(p * rf);
            const double log_factor = std::sqrt(p * rf / (2.0 * M_PI));
            int k = 0, peak_good = 0, below = 0;
            double selected80 = 0, rejected80 = 0;
            // R sum on this platform accumulates long double and returns
            // double. Preserve its two separate sum reductions and rounding.
            long double sum_log = 0, sum_residual = 0;
            for (int i = 0; i < h.bins; ++i) {
                const double m = work.pred[i] * p * rf;
                const double d = rf * h.obs[i];
                const double width = h.z * work.root[i] * sqrt_pr;
                below += d < m - width;
                if (work.pred[i] >= 20.0 && d <= m + p * width && d >= m - width) {
                    ++k;
                    peak_good += work.peak95[i];
                    if (work.peak80[i]) selected80 += h.obs[i];
                    sum_log += std::log(log_factor * work.root[i]);
                    const double residual = d - m;
                    sum_residual += (-0.5 * (residual * residual)) / m;
                } else if (work.peak80[i]) {
                    rejected80 += h.obs[i];
                }
            }
            // The rf=1 iteration supplies the decision for the next P.
            advance = below <= h.max_below;
            if (k <= h.nominal / 32.0 || !(peak_good >= 0.2 * peak95_count || peak95_count == 1))
                continue;
            const double peak_log = std::log(penalty(selected80 / rejected80));
            const double cost = -(static_cast<double>(sum_log) + k * (peak_log + tail_log_l + tail_log_r)
                                + static_cast<double>(sum_residual)) / std::sqrt(k);
            if (std::isfinite(cost) && cost < best.cost)
                best = {p, cost, rf, static_cast<double>(k)};
        }
        if (!advance) break;
    }
    return best;
}
}  // namespace

extern "C" SEXP stage3_hist_profiles(SEXP lambda, SEXP mu, SEXP sigma, SEXP hist, SEXP lookup) {
    try {
        const Histogram h(Rf_asReal(lambda), hist, lookup);
        Values means = numbers(mu), scales = numbers(sigma);
        if (means.size() != scales.size() || means.size() > static_cast<size_t>(INT_MAX))
            throw std::invalid_argument("mu and sigma must be paired");
        const int n = static_cast<int>(means.size());
        SEXP result = PROTECT(Rf_allocMatrix(REALSXP, n, 4));
        double* out = REAL(result);
        Buffer work(h.bins);
        for (int i = 0; i < n; ++i) {
            const Profile best = profile(h, means[i], scales[i], work);
            out[i] = best.p;
            out[i + n] = best.cost;
            out[i + 2*n] = best.rf;
            out[i + 3*n] = best.k;
        }
        UNPROTECT(1);
        return result;
    } catch (const std::exception& e) {
        Rf_error("stage3_hist_profiles: %s", e.what());
    }
    return R_NilValue;
}
