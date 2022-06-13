# MY scripts
import topic_finder
# Everything else
from flask import Flask, request, render_template
from flask_restful import reqparse
import os
import json


app = Flask(__name__)

@app.route('/')
def index():
    if 'keyword' in request.args and request.args['keyword'] != '':
        keyword = request.args['keyword']
        # Let's get the headings from the top 10 results + also ak
        headings = topic_finder.get_headings(keyword)
        return """
        <html>
        <head>
        <title>Topic Finder</title>
        </head>
        <body>
        <h1>"""\
        + keyword + \
        """</h1>
        """\
        + str(headings) + \
        """</h1>
        </body>
        </html>
        """ % (keyword, headings), 200, {'Content-Type': 'text/html'}
    else:
        # flask render form.html
        return render_template('form.html'), 200, {'Content-Type': 'text/html'}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
