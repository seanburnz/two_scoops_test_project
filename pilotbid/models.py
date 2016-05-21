from __future__ import unicode_literals

from django.db import models

# Create your models here.
import datetime
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

# Create your models here.


def validate_status(value):
    # validates a pilot status as Captain, First Officer or Seasonal
    if value not in ["CA","FO","SE"]:
        raise ValidationError('enter a valid status, e.g CA, FO, SE')


"""
Seniority List Models
"""

@python_2_unicode_compatible
class Pilot(models.Model):
    """ A model describing an individual pilot who may be included in any number of seniority lists for bidding
    """
    ecrew_id = models.IntegerField('ecrew ID', primary_key=True)
    email = models.CharField('email', max_length=100, validators=[validate_email])
    first_name = models.CharField('first name', max_length=100)
    last_name = models.CharField('last name', max_length=100)

    def __str__(self):
        return self.first_name + " " + self.last_name\


@python_2_unicode_compatible
class SeniorityList(models.Model):
    """ A model describing an individual instance of the seniority list which can be used to run a bid
    A seniority list has zero to many seniority list entries
    """
    description = models.CharField('description', max_length=100)  # e.g. 'Seniority List v52' or '2015 Summer Bid List'

    def __str__(self):
        return self.description


@python_2_unicode_compatible
class SeniorityListEntry(models.Model):
    """ A model describing an entry in a seniority list, the same pilot can be in multiple
    seniority lists with different status (eg after upgrade) but only once in any seniority list
    """
    seniority_list = models.ForeignKey(SeniorityList, on_delete=models.CASCADE)
    pilot = models.ForeignKey(Pilot, on_delete=models.CASCADE)  # unique for seniority_list
    master_seniority = models.IntegerField('master seniority')  # unique for seniority_list
    captain_seniority = models.IntegerField('captain seniority')  # unique for seniority_list
    status = models.CharField('status', max_length=2, validators=[validate_status])  # CA(ptain)/FO/SE(asonal)

    def __str__(self):
        return self.pilot.last_name + self.pilot.first_name


"""
Bid Models
"""

@python_2_unicode_compatible
class BidType(models.Model):
    """ A model describing a type of bid which will determine which bidding rules or 'options' are applicable
    Examples could include a vacation bid, upgrade bid or a deployment bid
    """
    description = models.CharField('description', max_length=50)  # e.g. Summer Deployment

    def __str__(self):
        return self.description


@python_2_unicode_compatible
class BidTypeOption(models.Model):
    """ A model describing bidding rules or options for a particular bid type
    Examples might be using master seniority instead of captain seniority, or allowing full terms to trump
    half terms etc
    """
    bid_type = models.ForeignKey(BidType, on_delete=models.CASCADE)  # e.g. Summer Bid
    option_name = models.CharField('option', max_length=50)  # e.g. Full term trumps
    description = models.CharField('description', max_length=200)  # More detailed description if necessary
    option_true_false = models.BooleanField('option is true/false')  # e.g. True
    option_value = models.IntegerField('value')  # e.g. 0, 1, 23

    def __str__(self):
        return self.option_name


@python_2_unicode_compatible
class Bid(models.Model):
    """ A model describing a bid published by the operator for seniority bidding by employees
    """
    bid_type = models.ForeignKey(BidType, on_delete=models.CASCADE)  # e.g. upgrade, summer deployment etc.
    seniority_list = models.ForeignKey(SeniorityList)  # seniority list being used to determine bid results
    open_date = models.DateTimeField('bid open date')  # date that bidding can begin
    close_date = models.DateTimeField('bid close date')  # date that bidding ends

    def __str__(self):
        return self.bid_type.description + ", " and self.open_date


@python_2_unicode_compatible
class BidChoice(models.Model):
    """ A model describing available choices for a particular bid and the number of places available
    """
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE)
    choice = models.CharField(max_length=10)  # short form option, e.g. YVR
    description = models.CharField(max_length=100)  # long form option, e.g Vancouver Base
    start_date = models.DateField()  # date that the position commences
    end_date = models.DateField()  # date that the position ends
    status = models.CharField(max_length=2, validators=[validate_status])  # pilot status, e.g. CA
    available_places = models.IntegerField()  # number of spots open for bidding, eg 14 (CA spots in YVR for bid period)

    def __str__(self):
        return self.description


class BidSubmission(models.Model):
    """ A model describing a submission in a bid with a timestamp and a list of bid submission priorities
    """
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE)
    pilot = models.ForeignKey(Pilot, on_delete=models.CASCADE)
    timestamp = models.DateTimeField('submission time', auto_now=True)  # time submitted


class SubmissionChoicePriority(models.Model):
    """ A model describing a priority for a bid choice in a given bid submission
    """
    bid_submission = models.ForeignKey(BidSubmission, on_delete=models.CASCADE)
    bid_choice = models.ForeignKey(BidChoice, on_delete=models.CASCADE)
    priority = models.IntegerField('priority')  # unique for bid_submission (preference order)