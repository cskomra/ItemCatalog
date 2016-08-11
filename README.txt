# Lifrary
####(a.k.a. Udacity's Fullstack Item Catalog project)

Lifrary is a web application based on Udacity's Fullstack Item Catalog project. It's purpose is to capture the stories of our lives in collections of different users' story "Tellings." A collection of user Tellings is called an "Event".   A collection of Events is called a "Story".

## Project Description

Lifrary provides for the creation of a list of Tellings (items) within a variety of Events (categories) and integrates Google+ and Facebook login (third party user registration and authentication).  Authenticated users have the ability post, edit, and delete their own Tellings (items) and Events.

## Basic functionality:
- Read without logging in.
- Log in with either Google+ or Facebook Login in order to create, edit, or delete Events and Tellings.
- Create, edit, or delete your own Event or Telling within the Story.
- Use the Story (home page) top menu to create a new Event for the Story.
- Click on any Event to open it and read its Tellings.
- Manage your Events from the Story page.
- Use the Event top menu to create a new Telling for that Event.
- Manage your Tellings from the Event page.

##Advanced Functionality
The following API endpoints have been made available:

**GET all events:**

    /events/JSON
**GET a specific event:**

    /events/<int:event_id>/event/JSON

**GET all tellings for a specific event:**

    /events/<int:event_id>/tellings/JSON

**GET a specific telling for a specific event:**

    /events/<int:event_id>/telling/<int:telling_id>/JSON


##Special considerations:

 - Media handling is demo'd; but not fully implemented.  Future plans are to validate the filetype and handle all types of media to enhance "Telling the Story".
 - Currently, there is only one main "Story".


##Technical Requirements:

 - [Python](https://www.python.org/downloads/release/python-2712/)
 - [Flask](https://pypi.python.org/pypi/Flask#downloads)

Alternatively:
 - Utilize Udacity's virtual machine environment here: [fullstack-nanodegree-vm](https://www.udacity.com/wiki/ud088/vagrant?_ga=1.193906725.946063065.1463769256)


##Sh...Sh..SSH...It's a Secret!
Required files containing client IDs and secrets have been removed from this repository.  Instructions for adding your own IDs and secrets are included below.  The application will not function properly without them.


### How to run:

 1. Once your technical environment is set up, download all files from the project into your project directory.
 2. In `finalproject.py` set `app.secret_key` to a key string of your choice.
 3. Create your [Google Client Id and Secret](https://classroom.udacity.com/nanodegrees/nd004/parts/0041345408/modules/348776022975461/lessons/3967218625/concepts/39636486130923#) and store the resulting `client_secrets.json` file in your project directory.
 4. [Register your version of the app with Facebook](https://classroom.udacity.com/nanodegrees/nd004/parts/0041345408/modules/348776022975461/lessons/3951228603/concepts/39497787740923#) and store the resulting `fb_client_secrets.json` file in your project directory.
 2. At your Python prompt, navigate to your project directory and run:  `python finalproject.py`.
 3.  The application will be accessible at  `http://localhost:5001`.