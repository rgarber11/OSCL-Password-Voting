# OSCL Password Voting

This main.py was used for Elections at the 2020-21 OSCL GA II. It takes a list of emails, generates a list of UUIDs, one for each email, and sends the entire list to an email. It then shuffles the list of emails and the list of UUIDs, and sends a randomized UUID to each email. It then deletes all emails that the script sent from "Sent Emails" so the UUIDs aren't traceable.

This was created using Python 3.9 and the GMail v1 API.

---

I wrote this program as a freshman in college, with very little actual Python knowledge. This current version is new and improved (with the lens of 3 years of study), though I have kept the original in the repo. Note that I still think this sort of password idea is a good medium-security voting strategy.
