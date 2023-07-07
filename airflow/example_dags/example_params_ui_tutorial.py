#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""DAG demonstrating various options for a trigger form generated by DAG params.

The DAG attribute `params` is used to define a default dictionary of parameters which are usually passed
to the DAG and which are used to render a trigger form.
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path

from airflow import DAG
from airflow.decorators import task
from airflow.exceptions import AirflowSkipException
from airflow.models.dagrun import DagRun
from airflow.models.param import Param
from airflow.models.taskinstance import TaskInstance

with DAG(
    dag_id=Path(__file__).stem,
    description=__doc__[0 : __doc__.find(".")],
    doc_md=__doc__,
    schedule=None,
    start_date=datetime.datetime(2022, 3, 4),
    catchup=False,
    tags=["example_ui"],
    params={
        # Let's start simple: Standard dict values are detected from type and offered as entry form fields.
        # Detected types are numbers, text, boolean, lists and dicts.
        # Note that such auto-detected parameters are treated as optional (not required to contain a value)
        "x": 3,
        "text": "Hello World!",
        "flag": False,
        "a_simple_list": ["one", "two", "three", "actually one value is made per line"],
        # But of course you might want to have it nicer! Let's add some description to parameters.
        # Note if you can add any HTML formatting to the description, you need to use the description_html
        # attribute.
        "most_loved_number": Param(
            42,
            type="integer",
            title="You favorite number",
            description_html="""Everybody should have a favorite number. Not only math teachers.
            If you can not think of any at the moment please think of the 42 which is very famous because
            of the book
            <a href='https://en.wikipedia.org/wiki/Phrases_from_The_Hitchhiker%27s_Guide_to_the_Galaxy#
            The_Answer_to_the_Ultimate_Question_of_Life,_the_Universe,_and_Everything_is_42'>
            The Hitchhiker's Guide to the Galaxy</a>""",
        ),
        # If you want to have a selection list box then you can use the enum feature of JSON schema
        "pick_one": Param(
            "value 42",
            type="string",
            title="Select one Value",
            description="You can use JSON schema enum's to generate drop down selection boxes.",
            enum=[f"value {i}" for i in range(16, 64)],
        ),
        # Boolean as proper parameter with description
        "bool": Param(
            True,
            type="boolean",
            title="Please confirm",
            description="A On/Off selection with a proper description.",
        ),
        # Dates and Times are also supported
        "date_time": Param(
            f"{datetime.date.today()}T{datetime.time(hour=12, minute=17, second=00)}+00:00",
            type="string",
            format="date-time",
            title="Date-Time Picker",
            description="Please select a date and time, use the button on the left for a pup-up calendar.",
        ),
        "date": Param(
            f"{datetime.date.today()}",
            type="string",
            format="date",
            title="Date Picker",
            description="Please select a date, use the button on the left for a pup-up calendar. "
            "See that here are no times!",
        ),
        "time": Param(
            f"{datetime.time(hour=12, minute=13, second=14)}",
            type=["string", "null"],
            format="time",
            title="Time Picker",
            description="Please select a time, use the button on the left for a pup-up tool.",
        ),
        # Fields can be required or not. If the defined fields are typed they are getting required by default
        # (else they would not pass JSON schema validation) - to make typed fields optional you must
        # permit the optional "null" type
        "required_field": Param(
            "You can not trigger if no text is given here!",
            type="string",
            title="Required text field",
            description="This field is required. You can not submit without having text in here.",
        ),
        "optional_field": Param(
            "optional text, you can trigger also w/o text",
            type=["null", "string"],
            title="Optional text field",
            description_html="This field is optional. As field content is JSON schema validated you must "
            "allow the <code>null</code> type.",
        ),
        # You can arrange the entry fields in sections so that you can have a better overview for the user
        # Therefore you can add the "section" attribute.
        # The benefit of the Params class definition is that the full scope of JSON schema validation
        # can be leveraged for form fields and they will be validated before DAG submission.
        "checked_text": Param(
            "length-checked-field",
            type="string",
            title="Text field with length check",
            description_html="""This field is required. And you need to provide something between 10 and 30
            characters. See the
            <a href='https://json-schema.org/understanding-json-schema/reference/string.html'>
            JSON schema description (string)</a> in for more details""",
            minLength=10,
            maxLength=20,
            section="JSON Schema validation options",
        ),
        "checked_number": Param(
            100,
            type="number",
            title="Number field with value check",
            description_html="""This field is required. You need to provide any number between 64 and 128.
            See the <a href='https://json-schema.org/understanding-json-schema/reference/numeric.html'>
            JSON schema description (numbers)</a> in for more details""",
            minimum=64,
            maximum=128,
            section="JSON Schema validation options",
        ),
        # Some further cool stuff as advanced options are also possible
        # You can have the user entering a dict object as a JSON with validation
        "object": Param(
            {"key": "value"},
            type=["object", "null"],
            title="JSON entry field",
            section="Special advanced stuff with form fields",
        ),
        # If you want to have static parameters which are always passed and not editable by the user
        # then you can use the JSON schema option of passing constant values. These parameters
        # will not be displayed but passed to the DAG
        "hidden_secret_field": Param("constant value", const="constant value"),
        # Finally besides the standard provided field generator you can have you own HTML form code
        # injected - but be careful, you can also mess-up the layout!
        "color_picker": Param(
            "#FF8800",
            type="string",
            title="Pick a color",
            description_html="""This is a special HTML widget as custom implementation in the DAG code.
            It is templated with the following parameter to render proper HTML form fields:
            <ul>
                <li><code>{name}</code>: Name of the HTML input field that is expected.</li>
                <li><code>{value}</code>:
                    (Default) value that should be displayed when showing/loading the form.</li>
                <li>Note: If you have elements changing a value, call <code>updateJSONconf()</code> to update
                    the form data to be posted as <code>dag_run.conf</code>.</li>
            </ul>
            Example: <code>&lt;input name='{name}' value='{value}' onchange='updateJSONconf()' /&gt;</code>
            """,
            custom_html_form="""
            <table width="100%" cellspacing="5"><tbody><tr><td>
                <label for="r_{name}">Red:</label>
            </td><td width="80%">
                <input id="r_{name}" type="range" min="0" max="255" value="0" onchange="u_{name}()"/>
            </td><td rowspan="3" style="padding-left: 10px;">
                <div id="preview_{name}"
                style="line-height: 40px; margin-bottom: 7px; width: 100%; background-color: {value};"
                >&nbsp;</div>
                <input class="form-control" type="text" maxlength="7" id="{name}" name="{name}"
                value="{value}" onchange="v_{name}()" />
            </td></tr><tr><td>
                <label for="g_{name}">Green:</label>
            </td><td>
                <input id="g_{name}" type="range" min="0" max="255" value="0" onchange="u_{name}()"/>
            </td></tr><tr><td>
                <label for="b_{name}">Blue:</label>
            </td><td>
                <input id="b_{name}" type="range" min="0" max="255" value="0" onchange="u_{name}()"/>
            </td></tr></tbody></table>
            <script lang="javascript">
                const hex_chars = "0123456789ABCDEF";
                function i2hex(name) {
                    var i = document.getElementById(name).value;
                    return hex_chars.substr(parseInt(i / 16), 1) + hex_chars.substr(parseInt(i % 16), 1)
                }
                function u_{name}() {
                    var hex_val = "#"+i2hex("r_{name}")+i2hex("g_{name}")+i2hex("b_{name}");
                    document.getElementById("{name}").value = hex_val;
                    document.getElementById("preview_{name}").style.background = hex_val;
                    updateJSONconf();
                }
                function hex2i(text) {
                    return hex_chars.indexOf(text.substr(0,1)) * 16 + hex_chars.indexOf(text.substr(1,1));
                }
                function v_{name}() {
                    var value = document.getElementById("{name}").value.toUpperCase();
                    document.getElementById("r_{name}").value = hex2i(value.substr(1,2));
                    document.getElementById("g_{name}").value = hex2i(value.substr(3,2));
                    document.getElementById("b_{name}").value = hex2i(value.substr(5,2));
                    document.getElementById("preview_{name}").style.background = value;
                }
                v_{name}();
            </script>""",
            section="Special advanced stuff with form fields",
        ),
    },
) as dag:

    @task(task_id="show_params")
    def show_params(**kwargs) -> None:
        ti: TaskInstance = kwargs["ti"]
        dag_run: DagRun = ti.dag_run
        if not dag_run.conf:
            print("Uups, no parameters supplied as DagRun.conf, was the trigger w/o form?")
            raise AirflowSkipException("No DagRun.conf parameters supplied.")
        print(f"This DAG was triggered with the following parameters:\n{json.dumps(dag_run.conf, indent=4)}")

    show_params()