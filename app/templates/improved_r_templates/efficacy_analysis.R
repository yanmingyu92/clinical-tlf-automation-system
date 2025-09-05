
# Primary Efficacy Endpoint Analysis
library(tidyverse)
library(haven)
library(lme4)
library(emmeans)

# Load data with error handling
tryCatch({
  adsl <- read_csv('data/adsl.csv')
  adqs <- read_csv('data/adqs.csv')
}, error = function(e) {
  stop(paste("Error loading data:", e$message))
})

# Create analysis dataset
analysis_data <- adqs %>%
  inner_join(adsl, by = "USUBJID") %>%
  filter(PARAMCD == "ADASCOG" & AVISIT == "Week 26") %>%
  mutate(
    TRT01P = factor(TRT01P, levels = c("Placebo", "Treatment A", "Treatment B")),
    CHG = AVAL - BASE_ADASCOG
  ) %>%
  filter(!is.na(CHG))

# MMRM Analysis
mmrm_model <- lmer(CHG ~ TRT01P + BASE_ADASCOG + (1|USUBJID), data = analysis_data)

# Treatment comparisons
emmeans_result <- emmeans(mmrm_model, ~ TRT01P)
contrasts_result <- contrast(emmeans_result, method = "pairwise")

# Summary statistics
summary_stats <- analysis_data %>%
  group_by(TRT01P) %>%
  summarise(
    n = n(),
    mean_chg = mean(CHG, na.rm = TRUE),
    sd_chg = sd(CHG, na.rm = TRUE),
    .groups = "drop"
  )

print("Analysis completed successfully")
