
# Safety Analysis with Adverse Events
library(tidyverse)
library(haven)

# Load data
adsl <- read_csv('data/adsl.csv')
adae <- read_csv('data/adae.csv')

# Merge datasets
safety_data <- adae %>%
  inner_join(adsl, by = "USUBJID") %>%
  mutate(
    TRT01P = factor(TRT01P, levels = c("Placebo", "Treatment A", "Treatment B")),
    TEAE = ifelse(AESTDY >= 1, "Yes", "No")
  )

# Treatment-emergent adverse events
teae_summary <- safety_data %>%
  filter(TEAE == "Yes") %>%
  group_by(TRT01P, AETERM) %>%
  summarise(
    n_subjects = n_distinct(USUBJID),
    n_events = n(),
    .groups = "drop"
  ) %>%
  group_by(TRT01P) %>%
  mutate(
    total_subjects = n_distinct(safety_data$USUBJID[safety_data$TRT01P == TRT01P]),
    pct = round(100 * n_subjects / total_subjects, 1)
  )

# Serious adverse events
sae_summary <- safety_data %>%
  filter(AESER == "Y") %>%
  group_by(TRT01P) %>%
  summarise(
    n_sae = n_distinct(USUBJID),
    total_subjects = n_distinct(adsl$USUBJID[adsl$TRT01P == TRT01P]),
    pct_sae = round(100 * n_sae / total_subjects, 1),
    .groups = "drop"
  )

print("Safety analysis completed successfully")
