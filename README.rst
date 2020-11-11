###############################
Google Calendar Suggester (GCS)
###############################

.. contents::

This script will give suggestions for free meeting slots for a group of people
needed for a meeting and who are working at Linaro. This feature exists to some
extent in the web version of Google calendar and is called "`suggested times`".
However, there are limitations with suggested times. You can only get the
information as an image and not as text. Also, you can only get a week at a
time and in addition to that you have to setup a "fake" meeting that you later
on need to throw away.

The use case for this script is when you have a need to arrange a meeting
consisting of a group of people from Linaro and people outside Linaro. It's
cumbersome and error prone to manually read from the calendar and write in an
email to the externals. With this script, you get suggestions on half an hour
basis for all the people that you intend to invite from Linaro. Everything in
text-format ready to be copy/pasted into the email with the external people
you're trying to agree on a day and time with for a meeting.

Installation
************
It's rather tricky to run Google API, but in short you will need to enable the
Google Calendar API and create an app at https://console.cloud.google.com and
setup OAuth2 credentials.

Create an app
=============
At https://console.cloud.google.com create a new project, give it meaningful
name (``Project name``), put it under ``linaro.org`` (``Organization``) and for
``Location``, browse and put the app under ``Engineering``.

Enable the Google Calendar API
==============================
At https://console.cloud.google.com, go to "APIs & Services > Library", and
search for ``Google Calendar API``, press it and press then ``Enable`` button.

Setup OATH2
===========
Go to https://console.cloud.google.com/apis/credentials and press ``+ CREATE
CREDENTIALS``, select ``OAuth client ID``. For ``Application type``, select
``Desktop app`` and give it a (any) name. Once completed you should find your
new Oauth2 credential under ``OAuth 2.0 Client IDs``. On the right side, press
the arrow to download this credential. Save the file for now, we will use it
later on.

Clone the script
================
.. code-block:: bash

    $ git clone https://github.com/jbech-linaro/gcs.git

Install necessary Python packages
=================================
.. code-block:: bash

    $ cd gcs
    $ pip install --user -r requirements.txt

Install the credentials
=======================
In the "Setup OATH2" step you downloaded a file, you need to move and rename the
file to the root of the "``gcs``" folder. The final name should be
``credentials.json``.

.. code-block:: bash

    $ mv <download-dir>/client_secret_9321...ontent.com.json credentials.json

Run
***
First time you run it the browser will open up and ask for permissions to run
the script. This will create a file called ``token.pickle``. After that the
script will work as expected.

Use cases
*********
Here are a couple of examples. There are default settings that will pick all
free slots for "joakim.bech" at the current day when the script is run and with
timezone UTC+1 (for now edit default setting in the script to your needs).

Get help
========
Simply call the script with ``-h``.

.. code-block:: bash

    $ ./gcs.py -h


Limit the time of day
=====================
Let's say that you are in Europe and want to invite people from US to the
meeting. Then you simply don't want to show all morning meetings, since that
would be in the middle of the night for the US people. By specifying ``-ne``
("no earlier than") and/or ``-nl`` ("no later than"). I.e., you can narrow down
things to a few hours.

.. code-block:: bash

    $ ./gcs.py -ne 14 -nl 19
    2020-11-10 14:00 UTC+1 (Tuesday)
    2020-11-10 14:30 UTC+1 (Tuesday)
    2020-11-10 15:00 UTC+1 (Tuesday)
    ...
    

Set start and end date
======================
By default the script uses the current day, but if you want to find a free slots
for more than the current day then you do that with ``-s`` and ``-e``. In the
example below we're combining it with the parameters from the previous example.

.. code-block:: bash

    $ ./gcs.py -ne 14 -nl 19 -s 2020-11-15 -e 2020-11-20
    2020-11-10 14:00 UTC+1 (Tuesday)
    2020-11-10 14:30 UTC+1 (Tuesday)
    2020-11-10 15:00 UTC+1 (Tuesday)
    ...

(In the example you get Saturdays and Sundays, in the future the will be possible
to remove those.)

If you omit the start ("``-s``"), then it'll use the current day. Meaning that
if you want to find a slot starting from "today" and X days in the future, then
you simply use the ``-e`` only. Example:

.. code-block:: bash

    $ ./gcs.py -ne 14 -nl 19 -e 2020-11-20
    ...


Add people to the planned meeting
=================================
This is main use case and idea for writing this script. I.e., try to find a free
slots for a group of people and get into text format. You do that by adding a
comma-separated list of first.last-names (no spaces after the comma!).

.. code-block:: bash

    $ ./gcs.py -ne 16 -nl 19 -s 2020-11-11 -e 2020-11-13 -p joakim.bech,david.brown,ryan.arnold
    2020-11-11 18:00 UTC+1 (Wednesday)
    2020-11-12 18:00 UTC+1 (Thursday)
    2020-11-13 16:00 UTC+1 (Friday)
    ...


List additional timezones
=========================
If you want to show the suggested slots in other timezones than your own default
timezone, then you can do that by adding UTC's after the "``-eu``" (extra UTCs).
Note that there is a limitation with the Python Argparser treating negative
numbers as parameters. The workaround will be shown as an example further down.

Here is an example to get the times UTC+2 and UTC-3 in addition to the default
timezone.

.. code-block:: bash

    $ ./gcs.py -eu 2,-3
    2020-11-11 08:00 UTC+1, 09:00 UTC+2, 04:00 UTC-3 (Wednesday)
    2020-11-11 08:30 UTC+1, 09:30 UTC+2, 04:30 UTC-3 (Wednesday)
    2020-11-11 09:00 UTC+1, 10:00 UTC+2, 05:00 UTC-3 (Wednesday)
    ...


Here is are a couple of examples on how to use negative numbers.

.. code-block:: bash

    # A single negative number [OK]
    $ ./gcs.py -eu -3
    2020-11-11 08:00 UTC+1, 04:00 UTC-3 (Wednesday)
    2020-11-11 08:30 UTC+1, 04:30 UTC-3 (Wednesday)
    2020-11-11 09:00 UTC+1, 05:00 UTC-3 (Wednesday)
    ...

    # Two negative number [NOK, argparser bug]
    $ ./gcs.py -eu -3,-4
    ...
    gcs.py: error: argument -eu/--extra-utc: expected one argument

    # Workaround for argparser bug when using two negative numbers
    $ ./gcs.py -eu 0,-3,-4
    2020-11-11 08:00 UTC+1, 07:00 UTC+0, 04:00 UTC-3, 03:00 UTC-4 (Wednesday)
    2020-11-11 08:30 UTC+1, 07:30 UTC+0, 04:30 UTC-3, 03:30 UTC-4 (Wednesday)
    2020-11-11 09:00 UTC+1, 08:00 UTC+0, 05:00 UTC-3, 04:00 UTC-4 (Wednesday)
    ...


ToDo
****
- Fix so you can add timezone as a parameter or config file.
- Give option to remove Saturdays and Sundays.
- Give option to get suggestions on hour basis instead of just half hour basis.
- Remove hard-code "joakim.bech" as the default person.
- General cleanup, since this was a quick and dirty hack, that nevertheless
  seems to work fine.
