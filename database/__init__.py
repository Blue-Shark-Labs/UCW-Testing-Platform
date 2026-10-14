# Database layer.
#
# Owns persistence: a PostgreSQL connection provider (raw SQL) plus
# migrations. Query functions (e.g. get_/create_) are added here per feature
# and are the only code that talks to the database.
