"""This file has a map dictionary to the name of tables for each sqlalchemy model,
    in the next phase we can use ambiguous table names and columns for more security!
"""

table_names = {
    "users": "users",
    "cex_accounts": "cex_accounts",
    "verifications": "verifications",
    "forget_requests": "forget_requests",
    "login_history": "login_history",
    "user_info": "user_info",
    "notifications": "notifications",
    "currencies": "currencies",
}
