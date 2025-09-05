
# Subgroup Analysis
library(tidyverse)
library(haven)
library(lme4)

# Load data
adsl <- read_csv('data/adsl.csv')
adqs <- read_csv('data/adqs.csv')

# Create analysis dataset
analysis_data <- adqs %>%
  inner_join(adsl, by = "USUBJID") %>%
  filter(PARAMCD == "ADASCOG" & AVISIT == "Week 26") %>%
  mutate(
    TRT01P = factor(TRT01P, levels = c("Placebo", "Treatment A", "Treatment B")),
    CHG = AVAL - BASE_ADASCOG,
    AGE_GROUP = case_when(
      AGE < 65 ~ "<65",
      AGE >= 65 & AGE < 75 ~ "65-75",
      AGE >= 75 ~ "¡Ý75"
    ),
    SEX_GROUP = SEX
  ) %>%
  filter(!is.na(CHG))

# Subgroup analyses
subgroup_results <- list()

# Age subgroups
age_subgroups <- analysis_data %>%
  group_by(AGE_GROUP, TRT01P) %>%
  summarise(
    n = n(),
    mean_chg = mean(CHG, na.rm = TRUE),
    sd_chg = sd(CHG, na.rm = TRUE),
    .groups = "drop"
  )

# Sex subgroups
sex_subgroups <- analysis_data %>%
  group_by(SEX_GROUP, TRT01P) %>%
  summarise(
    n = n(),
    mean_chg = mean(CHG, na.rm = TRUE),
    sd_chg = sd(CHG, na.rm = TRUE),
    .groups = "drop"
  )

# Interaction tests
age_interaction <- lm(CHG ~ TRT01P * AGE_GROUP, data = analysis_data)
sex_interaction <- lm(CHG ~ TRT01P * SEX_GROUP, data = analysis_data)

print("Subgroup analysis completed successfully")
