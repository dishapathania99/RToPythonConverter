# Create sample data
set.seed(123)
x <- rnorm(100)
y <- 2 * x + rnorm(100)

# Fit a linear model
model <- lm(y ~ x)

# View the model summary
summary(model)