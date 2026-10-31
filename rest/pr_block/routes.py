from flask import Blueprint, render_template

from rest.pr_block.pr_block import pr_block_route

pr_block = Blueprint(
    "pr_block",
    __name__,
    url_prefix="/pr-block",
)

pr_block.add_url_rule("/", view_func=pr_block_route, methods=["GET"])