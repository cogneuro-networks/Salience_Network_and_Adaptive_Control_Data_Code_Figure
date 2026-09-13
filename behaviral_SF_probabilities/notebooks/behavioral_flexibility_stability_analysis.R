# ==============================================================================
# Behavioral flexibility/stability task — statistics and main figure (2 × 2)
# Public supplement: reads data from data/ and writes figures to
# figures/ and session info to results/. See README.md for setup and data dictionary.
# ==============================================================================

suppressPackageStartupMessages({
  library(tidyverse)
  library(afex)
  library(effectsize)
  library(cowplot)
  library(ggdist)
  library(this.path)
})

args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)
root <- if (length(file_arg)) {
  dirname(normalizePath(sub("^--file=", "", file_arg[1]), winslash = "/"))
} else {
  getwd()
}
if (basename(root) == "notebooks") {
  root <- dirname(root)
}
setwd(root)

dir.create("figures", showWarnings = FALSE, recursive = TRUE)
dir.create("results", showWarnings = FALSE, recursive = TRUE)

# ---- Load data ----
combined <- readr::read_tsv("data/trials.tsv", show_col_types = FALSE) %>%
  dplyr::mutate(
    subject = factor(subject),
    trial = as.factor(trial),
    transition = factor(transition),
    long_short = factor(long_short),
    prob = factor(prob)
  ) %>%
  dplyr::select(subject, trial, transition, long_short, prob, acc, rt, base_rt, base_acc)

# ---- Accuracy: repeated-measures ANOVA (3 within-subject factors) ----
ACC_4factors <- combined %>%
  tidyr::drop_na(transition, acc)

contrasts(ACC_4factors$transition) <- contr.sum(2)
contrasts(ACC_4factors$long_short) <- contr.sum(2)
contrasts(ACC_4factors$prob) <- contr.sum(2)

anova_4factors_ACC <- afex::aov_ez(
  id = "subject",
  dv = "acc",
  data = ACC_4factors,
  within = c("transition", "long_short", "prob"),
  fun_aggregate = mean
)

acc_eta2 <- effectsize::eta_squared(
  anova_4factors_ACC, partial = TRUE, ci = 0.9, alternative = "two.sided"
)

# ---- RT transition cost: trial-level difference score ----
# Rules (see README): consecutive trials only; both ACC = 1; RT and base_rt > 150 ms;
# keep first row per trial block; exclude Baseline probability.
RT_cost <- combined %>%
  dplyr::group_by(subject) %>%
  dplyr::mutate(
    rt_diff = ifelse(
      dplyr::lag(base_acc) == 1 & acc == 1 & rt > 150 & dplyr::lag(base_rt) > 150,
      rt - dplyr::lag(base_rt),
      NA_real_
    )
  ) %>%
  dplyr::filter(trial != dplyr::lag(trial), prob != "Baseline", !is.na(rt_diff)) %>%
  tidyr::drop_na(transition, prob, long_short) %>%
  dplyr::ungroup()

contrasts(RT_cost$transition) <- contr.sum(2)
contrasts(RT_cost$long_short) <- contr.sum(2)
contrasts(RT_cost$prob) <- contr.sum(2)

anova_4factors_RT <- afex::aov_ez(
  id = "subject",
  dv = "rt_diff",
  data = RT_cost,
  within = c("transition", "long_short", "prob"),
  fun_aggregate = mean
)

rt_eta2 <- effectsize::eta_squared(
  anova_4factors_RT, partial = TRUE, ci = 0.9, alternative = "two.sided"
)

## Design-level labels (journal wording); only columns present in `d` are added
label_design_factors_safe <- function(d) {
  if ("transition" %in% names(d)) {
    d <- d %>% mutate(
      Domain = factor(
        transition,
        levels = c("flexibility", "stability"),
        labels = c("Task\nSwitching", "Distractor\nInhibition")
      )
    )
  }
  if ("long_short" %in% names(d)) {
    d <- d %>% mutate(
      Perturbation = factor(
        long_short,
        levels = c("Long", "Short"),
        labels = c("Low Density", "High Density")
      )
    )
  }
  if ("prob" %in% names(d)) {
    d <- d %>% mutate(
      Predictability = factor(
        prob,
        levels = c("prob_diff", "prob_same"),
        labels = c("High Predictability", "Low Predictability")
      )
    )
  }
  d
}

combined_lbl <- combined %>% label_design_factors_safe()
RT_cost_lbl <- RT_cost %>% label_design_factors_safe()

## ---- Morandi-style palette (low saturation) ----
col_task_switch <- "#D9A089" ## muted coral — task switching
col_dist_inhib <- "#5E7699" ## slate blue — distractor inhibition
## Names must match `Domain` factor *levels* from label_design_factors_safe() (line breaks in labels)
pal_domain_lines <- c(
  "Task\nSwitching" = col_task_switch,
  "Distractor\nInhibition" = col_dist_inhib
)
col_density_hi <- "#9B8AA6" ## muted purple — high density (Panel B, left half)
col_density_lo <- "#85A897" ## muted sage — low density (Panel B, right half)

pred_levels_plot <- c("Low Predictability", "High Predictability")
## X-axis tick labels (B/C/D only); factor levels in data stay `pred_levels_plot`
pred_x_labels <- c("Low Pred.", "High Pred.")

## a/c panel tags: npc y > 1 nudges label slightly above plot top
panel_tag_y_ac <- 1.0075

## Panel layout helpers (align y-axis column across 2×2 rows)
panel_left_inset_pt <- function(p) {
  g <- ggplotGrob(p)
  idx <- which(g$layout$name == "panel")[1L]
  col <- g$layout$l[idx]
  to_pt <- function(u) sum(as.numeric(grid::convertWidth(u, "pt", TRUE)))
  sum(to_pt(g$widths[seq_len(col - 1L)]))
}

panel_left_inset_npc <- function(p) {
  g <- ggplotGrob(p)
  idx <- which(g$layout$name == "panel")[1L]
  col <- g$layout$l[idx]
  to_pt <- function(u) sum(as.numeric(grid::convertWidth(u, "pt", TRUE)))
  widths_pt <- vapply(g$widths, to_pt, numeric(1))
  sum(widths_pt[seq_len(col - 1L)]) / sum(widths_pt)
}

## Match panel x (npc) to reference so cowplot rows share one y-axis column
align_panel_left_margin <- function(p, p_ref, top, right, bottom, left, search = c(-40, 160)) {
  target <- panel_left_inset_npc(p_ref)
  eval_npc <- function(l) {
    panel_left_inset_npc(p + theme(plot.margin = margin(top, right, bottom, l)))
  }
  if (abs(eval_npc(left) - target) < 1e-4) {
    return(margin(top, right, bottom, left))
  }
  lo <- search[1]
  hi <- search[2]
  for (i in seq_len(40L)) {
    mid <- (lo + hi) / 2
    if (eval_npc(mid) < target) lo <- mid else hi <- mid
  }
  margin(top, right, bottom, (lo + hi) / 2)
}

theme_main <- function(base_size = 12, base_family = "sans") {
  theme_classic(base_size = base_size, base_family = base_family) +
    theme(
      panel.grid = element_blank(),
      panel.border = element_blank(),
      axis.line = element_line(color = "black", linewidth = 0.45),
      axis.ticks = element_line(color = "black", linewidth = 0.4),
      axis.title = element_text(face = "bold", color = "black", size = rel(1.02)),
      axis.text = element_text(color = "black", size = rel(1)),
      plot.tag = element_text(face = "bold", size = base_size * 1.2 + 3),
      plot.background = element_rect(fill = NA, color = NA),
      panel.background = element_rect(fill = NA, color = NA),
      plot.margin = margin(10, 10, 8, 8),
      legend.position = "none"
    )
}

## Truncated axes (axis line only between outer breaks); tighter expand on A/B keeps end gaps modest
scale_y_ab_tight <- function() {
  ggplot2::scale_y_continuous(
    expand = ggplot2::expansion(mult = c(0.03, 0)),
    guide = ggplot2::guide_axis(cap = "both")
  )
}

## Symmetric x-axis span × fac (around midpoint of limits)
xlim_stretch <- function(lim, fac = 1.2) {
  m <- mean(lim)
  h <- diff(lim) / 2 * fac
  c(m - h, m + h)
}

## Shorten x-axis span (÷ fac) around same midpoint — ticks use more horizontal space
xlim_contract <- function(lim, fac = 1.5) {
  m <- mean(lim)
  h <- diff(lim) / 2 / fac
  c(m - h, m + h)
}

## ---- Panel A: half-density left; box + overlapping semi-transparent jittered rain on the right ----
rt_panel_A <- RT_cost_lbl %>%
  group_by(subject, Domain) %>%
  summarize(y = mean(rt_diff, na.rm = TRUE), .groups = "drop") %>%
  mutate(xn = as.numeric(Domain))

## ---- RT cell / ribbon ranges + CD x limits + shared y breaks for A/C/D (must precede pA) ----
rt_cell_CD <- RT_cost_lbl %>%
  group_by(subject, Domain, Perturbation, Predictability) %>%
  summarize(y = mean(rt_diff, na.rm = TRUE), .groups = "drop") %>%
  mutate(
    Predictability = factor(Predictability, levels = pred_levels_plot),
    xn = as.numeric(Predictability)
  )

rt_line_CD <- rt_cell_CD %>%
  group_by(Perturbation, Predictability, Domain) %>%
  summarize(
    m = mean(y, na.rm = TRUE),
    se = sd(y, na.rm = TRUE) / sqrt(n()),
    n = n(),
    .groups = "drop"
  ) %>%
  mutate(
    lo = m - qt(0.975, df = n - 1) * se,
    hi = m + qt(0.975, df = n - 1) * se,
    xn = as.numeric(Predictability)
  )

low_df <- rt_line_CD %>% dplyr::filter(Perturbation == "Low Density")
high_df <- rt_line_CD %>% dplyr::filter(Perturbation == "High Density")
low_sp <- rt_cell_CD %>% dplyr::filter(Perturbation == "Low Density")
high_sp <- rt_cell_CD %>% dplyr::filter(Perturbation == "High Density")

pred_hi <- pred_levels_plot[[2]]
cd_x_mid <- 1.5
cd_span <- 0.6
cd_xlim_lo <- 1 - cd_span / 2
cd_xlim_hi <- 2 + cd_span / 2
cd_xlim_full <- c(cd_xlim_lo, cd_xlim_hi)
## Direct labels: x in data units (~cd_span/26 per character); cumulative +7 chars right of original offset
cd_lbl_char_w <- cd_span / 26
cd_lbl_x <- 2 + 6 * cd_span / 34 + 5.5 * cd_lbl_char_w

## ---- C/D: very faint marginal RT density “ridges” at each Predictability x (behind lines/ribbons) ----
cd_ridge_x_bw <- 0.18
cd_ridge_x_dodge <- 0.055
cd_ridge_dens_adj <- 1.45
cd_ridge_alpha <- 0.14

cd_marginal_ridge_polygons <- function(sp_df,
                                       x_bw_scale = cd_ridge_x_bw,
                                       x_dodge = cd_ridge_x_dodge,
                                       dens_adj = cd_ridge_dens_adj,
                                       dens_n = 256L) {
  if (nrow(sp_df) < 2L) {
    return(tibble::tibble(
      xn = double(),
      x = double(),
      y = double(),
      Domain = factor(character(), levels = character()),
      gid = character()
    ))
  }
  sp_df <- sp_df %>%
    dplyr::mutate(
      Domain = droplevels(.data$Domain),
      xn = as.numeric(.data$xn)
    )
  dom_levels <- levels(sp_df$Domain)
  if (!length(dom_levels)) {
    return(tibble::tibble(
      xn = double(),
      x = double(),
      y = double(),
      Domain = factor(character(), levels = character()),
      gid = character()
    ))
  }
  out <- sp_df %>%
    dplyr::group_by(.data$xn, .data$Domain) %>%
    dplyr::group_modify(\(d, key) {
      yv <- d$y
      yv <- yv[is.finite(yv)]
      if (length(yv) < 2L) {
        return(tibble::tibble(x = double(), y = double()))
      }
      dn <- stats::density(yv, bw = "nrd0", adjust = dens_adj, n = dens_n, na.rm = TRUE)
      mw <- max(dn$y, na.rm = TRUE)
      if (!is.finite(mw) || mw <= 0) {
        return(tibble::tibble(x = double(), y = double()))
      }
      w <- dn$y / mw * x_bw_scale
      xc <- as.numeric(key$xn[[1]])
      dom <- as.character(key$Domain[[1]])
      di <- match(dom, dom_levels)
      if (is.na(di)) di <- 1L
      xc <- xc + (di - 1.5) * 2 * x_dodge
      tibble::tibble(
        x = c(xc - w, rev(xc + w)),
        y = c(dn$x, rev(dn$x))
      )
    }) %>%
    dplyr::ungroup() %>%
    dplyr::mutate(
      gid = interaction(.data$xn, .data$Domain, drop = TRUE)
    )
  out
}

## A/C/D share fixed RT y-axis: 0–600, ticks every 200 ms
ylim_rt_acd <- c(0, 600)
rt_y_breaks <- seq(0, 600, 200)

scale_y_rt_acd <- function() {
  ggplot2::scale_y_continuous(
    limits = ylim_rt_acd,
    breaks = rt_y_breaks,
    labels = scales::label_number(accuracy = 1),
    expand = ggplot2::expansion(mult = c(0, 0)),
    guide = ggplot2::guide_axis(cap = "both")
  )
}

make_direct_labels <- function(df_line) {
  df_line %>%
    dplyr::filter(as.character(Predictability) == pred_hi) %>%
    dplyr::mutate(
      lab = as.character(Domain),
      x = cd_lbl_x,
      y = m
    )
}

lbl_c <- make_direct_labels(low_df)
lbl_d <- make_direct_labels(high_df)

xnudge_v <- -0.26
xnudge_br <- 0.11
box_w_a <- 0.088
## Horizontal rain spread ≤ ~3 box widths; vertical jitter small (ms)
set.seed(84721)
rt_panel_A <- rt_panel_A %>%
  dplyr::mutate(
    xjit = stats::runif(dplyr::n(), -1.5 * box_w_a, 1.5 * box_w_a),
    yjit = stats::rnorm(dplyr::n(), 0, sd = 7)
  )

domain_x_labels <- levels(droplevels(RT_cost_lbl$Domain))

## C/D density banner text (annotate uses mm); B legend text uses pt
density_banner_size_mm <- 2.2 + 3 / ggplot2::.pt
density_banner_size_pt <- density_banner_size_mm * ggplot2::.pt

## Panel A: halfeye slab outline — share numeric stroke with boxplot (see geom_boxplot below)
pa_slab_lw <- 0.38
pa_slab_br <- alpha("grey22", 0.9)

pA <- ggplot(rt_panel_A, aes(y = y)) +
  ggdist::stat_halfeye(
    aes(x = xn, fill = Domain, color = Domain),
    adjust = 0.52,
    side = "left",
    width = 0.48,
    alpha = 0.62,
    justification = 0.5,
    .width = 0,
    slab_color = pa_slab_br,
    slab_linewidth = pa_slab_lw,
    position = ggplot2::position_nudge(x = xnudge_v),
    show_point = FALSE,
    show_interval = FALSE
  ) +
  geom_boxplot(
    aes(x = xn + xnudge_br, group = Domain, fill = Domain, color = Domain),
    width = box_w_a,
    alpha = 0.92,
    outlier.shape = NA,
    linewidth = pa_slab_lw,
    color = pa_slab_br,
    coef = 0
  ) +
  geom_point(
    aes(x = xn + xnudge_br + xjit, y = y + yjit, color = Domain),
    alpha = 0.38,
    size = 1.85,
    stroke = 0,
    shape = 16
  ) +
  scale_fill_manual(values = pal_domain_lines, guide = "none") +
  scale_color_manual(values = pal_domain_lines, guide = "none") +
  ggplot2::scale_x_continuous(
    breaks = seq_along(domain_x_labels),
    labels = domain_x_labels,
    expand = ggplot2::expansion(mult = c(0.06, 0)),
    guide = ggplot2::guide_axis(cap = "both")
  ) +
  scale_y_rt_acd() +
  ggplot2::coord_cartesian(ylim = ylim_rt_acd, xlim = c(0.6, 2.6), clip = "on") +
  labs(x = NULL, y = "RT Transition Cost (ms)", title = NULL, subtitle = NULL, tag = "a") +
  theme_main() +
  theme(
    plot.margin = margin(16, 28, 10, 8),
    plot.tag.position = c(0, panel_tag_y_ac),
    plot.tag = element_text(hjust = 0),
    axis.title.y = element_text(
      angle = 90,
      vjust = 0.5,
      hjust = 0.5,
      margin = margin(t = 10, r = 10, b = 6, l = 0)
    )
  )

## ---- Panel B: two x ticks only; at each Pred., left slab = low density, right = high density ----
acc_subj_B <- combined_lbl %>%
  drop_na(Perturbation, Predictability, acc) %>%
  group_by(subject, Perturbation, Predictability) %>%
  summarize(y = mean(acc, na.rm = TRUE), .groups = "drop") %>%
  mutate(
    Predictability = factor(Predictability, levels = pred_levels_plot),
    xn = as.numeric(Predictability)
  )

acc_B_lo <- dplyr::filter(acc_subj_B, Perturbation == "Low Density")
acc_B_hi <- dplyr::filter(acc_subj_B, Perturbation == "High Density")

acc_B_pair_pred <- acc_subj_B %>%
  tidyr::pivot_wider(
    id_cols = c(subject, Perturbation),
    names_from = Predictability,
    values_from = y
  ) %>%
  tidyr::drop_na(tidyselect::all_of(pred_levels_plot))

acc_B_mean_line <- acc_subj_B %>%
  dplyr::group_by(Perturbation, Predictability) %>%
  dplyr::summarize(m = mean(y, na.rm = TRUE), xn = dplyr::first(xn), .groups = "drop") %>%
  dplyr::arrange(Perturbation, xn)

ymin_b <- max(0.72, min(c(acc_subj_B$y), na.rm = TRUE) - 0.035)
ymax_b <- min(1.02, max(c(acc_subj_B$y), na.rm = TRUE) + 0.035)
ylim_b_raw <- c(ymin_b - 0.012, ymax_b + 0.012)
yb_mid <- mean(ylim_b_raw)
yb_half <- diff(ylim_b_raw) / 2 * 1.2
ylim_b <- c(yb_mid - yb_half, yb_mid + yb_half)

hw <- 0.44
xnudge_lo <- -0.2
xnudge_hi <- 0.2
pb_slab_lw <- 0.22

pB <- ggplot(acc_subj_B, aes(y = y)) +
  geom_segment(
    data = acc_B_pair_pred,
    aes(
      x = 1.05,
      xend = 1.95,
      y = .data[[pred_levels_plot[[1]]]],
      yend = .data[[pred_levels_plot[[2]]]],
      color = Perturbation
    ),
    inherit.aes = FALSE,
    linewidth = 0.38,
    alpha = 0.32,
    lineend = "round"
  ) +
  ggdist::stat_halfeye(
    data = acc_B_lo,
    aes(x = xn, y = y, fill = Perturbation),
    inherit.aes = FALSE,
    side = "left",
    width = hw,
    alpha = 0.52,
    justification = 0.5,
    adjust = 0.62,
    .width = 0,
    slab_color = alpha("grey28", 0.42),
    slab_linewidth = pb_slab_lw,
    position = ggplot2::position_nudge(x = xnudge_lo),
    show_point = FALSE,
    show_interval = FALSE
  ) +
  ggdist::stat_halfeye(
    data = acc_B_hi,
    aes(x = xn, y = y, fill = Perturbation),
    inherit.aes = FALSE,
    side = "right",
    width = hw,
    alpha = 0.52,
    justification = 0.5,
    adjust = 0.62,
    .width = 0,
    slab_color = alpha("grey28", 0.42),
    slab_linewidth = pb_slab_lw,
    position = ggplot2::position_nudge(x = xnudge_hi),
    show_point = FALSE,
    show_interval = FALSE
  ) +
  geom_line(
    data = acc_B_mean_line,
    aes(x = xn, y = m, color = Perturbation, group = Perturbation),
    inherit.aes = FALSE,
    linewidth = 0.56,
    alpha = 0.92,
    lineend = "round"
  ) +
  ggplot2::scale_fill_manual(
    values = c(`Low Density` = col_density_lo, `High Density` = col_density_hi),
    guide = ggplot2::guide_legend(
      title = NULL,
      nrow = 2,
      ncol = 1,
      byrow = TRUE,
      direction = "vertical",
      override.aes = list(alpha = 0.384, colour = NA)
    )
  ) +
  ggplot2::scale_color_manual(
    name = "Density",
    values = c(`Low Density` = col_density_lo, `High Density` = col_density_hi),
    guide = "none"
  ) +
  ggplot2::scale_x_continuous(
    breaks = 1:2,
    labels = pred_x_labels,
    expand = ggplot2::expansion(mult = c(0.03, 0)),
    guide = ggplot2::guide_axis(cap = "both")
  ) +
ggplot2::scale_y_continuous(
    breaks = seq(0.60, 1.00, by = 0.10), # 强制设定刻度为 0.6, 0.7, 0.8, 0.9, 1.0
    labels = scales::label_number(accuracy = 0.01),
    expand = ggplot2::expansion(mult = c(0, 0)), # 取消两端多余留白
    guide = ggplot2::guide_axis(cap = "both")    # 开启截断
  ) +
  ggplot2::coord_cartesian(
    xlim = xlim_contract(xlim_stretch(c(0.62, 2.38)), 1.5),
    ylim = c(0.60, 1.00)  # ⚠️ 关键点：把之前的 ylim_b 改成与 breaks 一致的硬范围！
  ) +
  labs(x = NULL, y = "Accuracy", title = NULL, subtitle = NULL, tag = "b")

pB_themed <- pB +
  theme_main() +
  theme(
    axis.title.y = element_text(
      angle = 90,
      vjust = 0.5,
      hjust = 0.5,
      margin = margin(t = 10, r = 10, b = 6, l = 0)
    ),
    legend.position = c(0.5, 0.075),
    legend.justification = c(0.5, 0),
    legend.background = element_rect(fill = NA, colour = NA),
    legend.box.background = element_rect(fill = NA, colour = NA),
    legend.key = element_rect(fill = NA, colour = NA),
    legend.text = element_text(color = alpha("grey28", 0.464), size = density_banner_size_pt),
    legend.margin = margin(2, 4, 4, 4),
    legend.spacing.y = grid::unit(9.504, "pt"),
    legend.key.spacing.y = grid::unit(14 * 0.6, "pt"),
    legend.key.height = unit(0.55, "lines"),
    legend.key.width = unit(0.55, "lines"),
    plot.margin = margin(16, 28, 10, 8)
  )

pB <- pB_themed +
  theme(
    plot.tag.position = c(0, 1),
    plot.tag = element_text(hjust = 0)
  )

## ---- Panels C & D: spaghetti + 95% ribbons + mean lines; direct labels (no legend) ----
build_panel_cd <- function(sp_df, ln_df, tag_ch, show_y_title, show_y_numbers, density_banner, lbl_df,
                           banner_size = density_banner_size_mm,
                           label_size = 2 + 3 / ggplot2::.pt) {
  yd_rt <- diff(ylim_rt_acd)
  ridge_df <- cd_marginal_ridge_polygons(sp_df)
  p_cd <- ggplot2::ggplot()
  if (nrow(ridge_df) > 0L) {
    p_cd <- p_cd + ggplot2::geom_polygon(
      data = ridge_df,
      ggplot2::aes(x = x, y = y, group = gid, fill = Domain),
      alpha = cd_ridge_alpha,
      colour = NA,
      linewidth = 0,
      inherit.aes = FALSE
    )
  }
  p_cd +
    ## Individual traces: same linewidth / lineend as Panel B `geom_segment` paired lines
    geom_line(
      data = sp_df,
      aes(x = xn, y = y, group = interaction(subject, Domain), color = Domain),
      linewidth = 0.38,
      alpha = 0.13,
      lineend = "round"
    ) +
    geom_ribbon(
      data = ln_df,
      aes(x = xn, ymin = lo, ymax = hi, fill = Domain, group = Domain),
      alpha = 0.26,
      color = NA
    ) +
    geom_line(
      data = ln_df,
      aes(x = xn, y = m, color = Domain, group = Domain),
      linewidth = 0.625
    ) +
    annotate(
      "text",
      x = cd_x_mid,
      y = ylim_rt_acd[2] - 0.028 * yd_rt,
      label = density_banner,
      fontface = "bold",
      size = banner_size,
      color = alpha("grey28", 0.78),
      hjust = 0.5,
      vjust = 1
    ) +
    geom_text(
      data = lbl_df,
      aes(x = x, y = y, label = lab, color = Domain),
      inherit.aes = FALSE,
      hjust = 0.5,
      vjust = 0.5,
      lineheight = 0.92,
      size = label_size,
      fontface = "italic",
      show.legend = FALSE
    ) +
    ggplot2::scale_x_continuous(
      breaks = 1:2,
      labels = pred_x_labels,
      limits = cd_xlim_full,
      expand = ggplot2::expansion(mult = c(0, 0)),
      guide = ggplot2::guide_axis(cap = "both")
    ) +
    scale_y_rt_acd() +
    scale_color_manual(values = pal_domain_lines, guide = "none") +
    scale_fill_manual(values = pal_domain_lines, guide = "none") +
    coord_cartesian(ylim = ylim_rt_acd, clip = "off", xlim = cd_xlim_full) +
    labs(
      x = NULL,
      y = if (show_y_title) "RT Transition Cost (ms)" else NULL,
      title = NULL,
      subtitle = NULL,
      tag = tag_ch
    ) +
    theme_main() +
    theme(
      plot.tag.position = if (!is.null(tag_ch)) c(0, panel_tag_y_ac) else c(0, 1),
      plot.tag = if (show_y_title) element_text(hjust = 0) else element_text(),
      plot.margin = margin(16, 28, 10, 8),
      axis.text.y = if (show_y_numbers) element_text() else element_blank(),
      axis.ticks.y = element_line(),
      axis.ticks.length.y = grid::unit(3.8, "pt"),
      axis.title.y = if (show_y_title) {
        element_text(
          angle = 90,
          vjust = 0.5,
          hjust = 0.5,
          margin = margin(t = 10, r = 10, b = 6, l = 0)
        )
      } else {
        element_blank()
      }
    )
}

pC <- build_panel_cd(
  low_sp, low_df, "c", TRUE, TRUE, "Low Density", lbl_c,
  label_size = 2 + 3 / ggplot2::.pt
)
pD <- build_panel_cd(
  high_sp, high_df, NULL, FALSE, FALSE, "High Density", lbl_d,
  label_size = 2 + 3 / ggplot2::.pt
)

## Open a null device before ggplotGrob / grid::convertWidth / cowplot.
## Under non-interactive Rscript, the first drawing otherwise creates Rplots.pdf.
grDevices::pdf(NULL)

## A/C and B/D: match panel y-axis column across rows (cowplot only aligns within each row)
pC <- pC + theme(plot.margin = align_panel_left_margin(pC, pA, 16, 28, 10, 8))
pD <- pD + theme(plot.margin = align_panel_left_margin(pD, pB, 16, 28, 10, 8))

## ---- Assemble 2 \u00d7 2 (no outer titles; direct labeling only) ----
## patchwork 只对齐全图边界；B 有图例时 ggplot 的 panel 高度常与 A 不一致。
## cowplot::plot_grid(align = "hv", axis = "tblr") 按面板边界对齐顶/底（及左右）。
fig_top <- cowplot::plot_grid(pA, pB, nrow = 1, rel_widths = c(1, 1), align = "hv", axis = "tblr")
fig_bot <- cowplot::plot_grid(pC, pD, nrow = 1, rel_widths = c(1, 1), align = "hv", axis = "tblr")
fig_main <- cowplot::plot_grid(fig_top, fig_bot, ncol = 1, rel_heights = c(1, 1), align = "v")
grDevices::dev.off()

out_main_pdf <- "figures/main_figure_2x2.pdf"
out_main_png <- "figures/main_figure_2x2.png"
out_main_eps <- "figures/main_figure_2x2.eps"
out_main_svg <- "figures/main_figure_2x2.svg"
## Write via tempdir() first: some Windows graphics devices fail on Unicode project paths,
## then copy into the project folder (file.copy handles UTF-8 paths better than some devices).
ggsave_figures_main <- function() {
  w <- 10.2 * 0.6
  h <- 10.4 * 0.6
  tmp_pdf <- tempfile("main_figure_2x2_", fileext = ".pdf")
  tmp_png <- tempfile("main_figure_2x2_", fileext = ".png")
  tmp_eps <- tempfile("main_figure_2x2_", fileext = ".eps")
  tmp_svg <- tempfile("main_figure_2x2_", fileext = ".svg")
  on.exit(
    {
      unlink(c(tmp_pdf, tmp_png, tmp_eps, tmp_svg))
    },
    add = TRUE
  )
  tryCatch(
    ggsave(
      tmp_pdf, fig_main, width = w, height = h,
      device = grDevices::cairo_pdf, bg = "transparent"
    ),
    error = function(e) {
      message("cairo_pdf failed (", conditionMessage(e), "); using pdf() instead.")
      ggsave(
        tmp_pdf, fig_main, width = w, height = h,
        device = grDevices::pdf, bg = "white", useDingbats = FALSE
      )
    }
  )
  tryCatch(
    ggsave(
      tmp_png, fig_main, width = w, height = h, dpi = 500,
      bg = "transparent", device = grDevices::png, type = "cairo"
    ),
    error = function(e) {
      message("cairo png failed (", conditionMessage(e), "); using png() without cairo.")
      ggsave(
        tmp_png, fig_main, width = w, height = h, dpi = 500,
        bg = "white", device = grDevices::png
      )
    }
  )
  tryCatch(
    ggsave(
      tmp_eps, fig_main, width = w, height = h,
      device = grDevices::cairo_ps, bg = "transparent"
    ),
    error = function(e) {
      message("cairo_ps failed (", conditionMessage(e), "); using postscript() instead.")
      ggsave(
        tmp_eps, fig_main, width = w, height = h,
        device = grDevices::postscript, bg = "white", horizontal = FALSE, paper = "special"
      )
    }
  )
  tryCatch(
    ggsave(
      tmp_svg, fig_main, width = w, height = h,
      device = grDevices::svg, bg = "transparent"
    ),
    error = function(e) {
      if (!requireNamespace("svglite", quietly = TRUE)) {
        stop("SVG export failed and svglite is not installed: ", conditionMessage(e))
      }
      ggsave(
        tmp_svg, fig_main, width = w, height = h,
        device = svglite::svglite, bg = "transparent"
      )
    }
  )
  copy_or_warn <- function(from, to, kind) {
    if (file.exists(to)) {
      try(unlink(to), silent = TRUE)
    }
    if (isTRUE(file.copy(from, to, overwrite = TRUE))) {
      return(to)
    }
    alt <- file.path(tempdir(), basename(to))
    if (isTRUE(file.copy(from, alt, overwrite = TRUE))) {
      warning(
        "Could not write ", kind, " to project folder (permission or file lock). ",
        "Saved copy to: ", alt,
        call. = FALSE
      )
      return(alt)
    }
    stop("Could not copy ", kind, " to ", to, " or to tempdir.")
  }
  list(
    pdf = copy_or_warn(tmp_pdf, out_main_pdf, "PDF"),
    png = copy_or_warn(tmp_png, out_main_png, "PNG"),
    eps = copy_or_warn(tmp_eps, out_main_eps, "EPS"),
    svg = copy_or_warn(tmp_svg, out_main_svg, "SVG")
  )
}
fig_saved <- ggsave_figures_main()
for (fmt in fig_saved) {
  message("Saved: ", normalizePath(fmt, winslash = "/", mustWork = FALSE))
}

sink("results/sessionInfo.txt")
print(sessionInfo())
sink()
message("Saved: ", normalizePath("results/sessionInfo.txt", winslash = "/", mustWork = FALSE))
