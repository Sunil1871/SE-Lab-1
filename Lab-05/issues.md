# Issues Fixed in Subscription Billing System

| No. | Issue | Fix Applied |
|---|---|---|
| 1 | Hardcoded webhook secret | Read the secret from an environment variable. |
| 2 | Hardcoded encryption key | Read the encryption key from an environment variable. |
| 3 | Weak random coupon generation | Used the `secrets` module. |
| 4 | Incorrect trial expiry check | Corrected the trial period condition. |
| 5 | Coupon could exceed 100% | Limited the discount to 100%. |
| 6 | Incorrect retry limit | Limited payment attempts to three. |
| 7 | Billing date failed at month end | Handled different month lengths. |
| 8 | Unsafe HTML output | Escaped user input in the invoice template. |
| 9 | Unsafe XML parsing settings | Disabled external entity resolution and network access. |
| 10 | Unsafe signature comparison | Used `hmac.compare_digest()`. |
| 11 | Negative invoice amount | Added validation to reject negative amounts. |
| 12 | Insecure encryption mode | Replaced AES-ECB with authenticated AES-GCM encryption. |

## Result

Static analysis was performed using Pylint, Bandit, and Flake8. The Pylint score reached 10.00/10 after code-quality fixes.