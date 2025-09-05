
# Demographic and Baseline Characteristics
library(tidyverse)
library(haven)

# Load data
adsl <- read_csv('data/adsl.csv')

# Create demographic summary
demographic_summary <- adsl %>%
  filter(ITTFL == "Y") %>%
  mutate(
    TRT01P = factor(TRT01P, levels = c("Placebo", "Treatment A", "Treatment B")),
    AGE_CAT = case_when(
      AGE < 65 ~ "<65",
      AGE >= 65 & AGE < 75 ~ "65-75",
      AGE >= 75 ~ "¡Ý75",
      TRUE ~ NA_character_
    )
  ) %>%
  group_by(TRT01P) %>%
  summarise(
    n = n(),
    mean_age = mean(AGE, na.rm = TRUE),
    sd_age = sd(AGE, na.rm = TRUE),
    pct_male = round(100 * sum(SEX == "M", na.rm = TRUE) / n, 1),
    mean_bmi = mean(BMIBL, na.rm = TRUE),
    sd_bmi = sd(BMIBL, na.rm = TRUE),
    .groups = "drop"
  )

# Categorical variables
categorical_summary <- adsl %>%
  filter(ITTFL == "Y") %>%
  mutate(TRT01P = factor(TRT01P, levels = c("Placebo", "Treatment A", "Treatment B"))) %>%
  group_by(TRT01P, SEX) %>%
  summarise(n = n(), .groups = "drop") %>%
  group_by(TRT01P) %>%
  mutate(
    total = sum(n),
    pct = round(100 * n / total, 1)
  )

print("Demographic analysis completed successfully")
