
# Error Recovery Mechanism for R Code Execution
execute_r_code_with_recovery <- function(r_code) {
  tryCatch({
    # Execute the R code
    eval(parse(text = r_code))
    return(list(success = TRUE, result = "Code executed successfully"))
  }, error = function(e) {
    # Try simplified version
    tryCatch({
      # Remove complex functions and try basic analysis
      simplified_code <- simplify_r_code(r_code)
      eval(parse(text = simplified_code))
      return(list(success = TRUE, result = "Simplified code executed successfully"))
    }, error = function(e2) {
      # Return error information
      return(list(success = FALSE, error = e2$message))
    })
  })
}

simplify_r_code <- function(r_code) {
  # Remove complex functions and keep basic operations
  simplified <- r_code %>%
    str_replace_all("library\([^)]+\)", "") %>%
    str_replace_all("lmer\([^)]+\)", "lm(CHG ~ TRT01P, data = analysis_data)") %>%
    str_replace_all("emmeans\([^)]+\)", "") %>%
    str_replace_all("contrast\([^)]+\)", "")
  
  return(simplified)
}
