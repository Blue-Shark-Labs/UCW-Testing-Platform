# Use case layer.
#
# Orchestrates database-layer calls for the REST layer. Holds business logic
# that is independent of HTTP (REST) and SQL (database) specifics.
#
# Belongs here: business rules and orchestration (e.g. auth attempt/lockout
# checks, question selection, scoring) and calls into database/ functions.
# Does not belong here: Flask/HTTP objects (request, render_template, jsonify)
# or raw SQL — those stay in rest/ and database/ respectively.
