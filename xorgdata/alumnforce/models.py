from django.db import models
from django.utils.translation import ugettext_lazy as _

from xorgdata.utils.fields import DottedSlugField, UnboundedCharField


class Account(models.Model):
    af_id = models.IntegerField(primary_key=True)
    ax_id = models.CharField(max_length=20, blank=True, null=True, unique=True)
    first_name = UnboundedCharField()
    last_name = UnboundedCharField()
    common_name = UnboundedCharField(blank=True)
    civility = UnboundedCharField(blank=True)
    birthdate = models.DateField(blank=True, null=True)
    address_1 = UnboundedCharField(blank=True)
    address_2 = UnboundedCharField(blank=True)
    address_3 = UnboundedCharField(blank=True)
    address_4 = UnboundedCharField(blank=True)
    address_postcode = UnboundedCharField(blank=True)
    address_city = UnboundedCharField(blank=True)
    address_state = UnboundedCharField(blank=True)
    address_country = models.CharField(max_length=2, blank=True)
    address_npai = models.NullBooleanField()
    phone_personnal = UnboundedCharField(blank=True)
    phone_mobile = UnboundedCharField(blank=True)
    email_1 = models.EmailField()
    email_2 = models.EmailField(blank=True)
    nationality = UnboundedCharField(blank=True)
    nationality_2 = UnboundedCharField(blank=True)
    nationality_3 = UnboundedCharField(blank=True)
    dead = models.NullBooleanField()
    deathdate = models.DateField(blank=True, null=True)
    dead_for_france = UnboundedCharField(blank=True)
    user_kind = models.IntegerField()
    additional_roles = models.IntegerField(blank=True, null=True)
    xorg_id = DottedSlugField(unique=True, max_length=255)
    school_id = UnboundedCharField(blank=True)
    admission_path = UnboundedCharField(blank=True)
    cursus_domain = UnboundedCharField(blank=True)
    cursus_name = UnboundedCharField(blank=True)
    corps_current = UnboundedCharField(blank=True)
    corps_origin = UnboundedCharField(blank=True)
    corps_grade = UnboundedCharField(blank=True)
    nickname = UnboundedCharField(blank=True)
    sport_section = UnboundedCharField(blank=True)
    binets = UnboundedCharField(blank=True)
    mail_reception = UnboundedCharField(blank=True)
    newsletter_inscriptions = UnboundedCharField(blank=True)
    profile_picture_url = UnboundedCharField(blank=True)

    def __str__(self):
        if self.ax_id:
            return "%s (AX ID %s)" % (self.xorg_id, self.ax_id)
        return self.xorg_id


class AcademicInformation(models.Model):
    account = models.ForeignKey('Account', on_delete=models.CASCADE)
    diploma_reference = UnboundedCharField()
    diplomed = models.BooleanField()
    diplomation_date = models.DateField()
    cycle = UnboundedCharField(blank=True)
    domain = UnboundedCharField(blank=True)
    name = UnboundedCharField(blank=True)


class ProfessionnalInformation(models.Model):
    account = models.ForeignKey('Account', on_delete=models.CASCADE)
    title = UnboundedCharField()
    role = UnboundedCharField(blank=True)
    company_name = UnboundedCharField()
    address_1 = UnboundedCharField(blank=True)
    address_2 = UnboundedCharField(blank=True)
    address_3 = UnboundedCharField(blank=True)
    address_4 = UnboundedCharField(blank=True)
    address_postcode = UnboundedCharField(blank=True)
    address_city = UnboundedCharField(blank=True)
    address_country = UnboundedCharField(blank=True)
    phone_indicator = models.IntegerField(blank=True, null=True)
    phone_number = UnboundedCharField(blank=True)
    mobile_phone_indicator = models.IntegerField(blank=True, null=True)
    mobile_phone_number = UnboundedCharField(blank=True)
    fax = UnboundedCharField(blank=True)
    email = models.EmailField(blank=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    contract_kind = UnboundedCharField(blank=True)
    current = models.NullBooleanField()
    creator_of_company = models.NullBooleanField()
    buyer_of_company = models.NullBooleanField()


class Group(models.Model):
    af_id = models.IntegerField(primary_key=True)
    ax_id = models.CharField(max_length=20, blank=True, null=True, unique=True)
    url = UnboundedCharField(blank=True)
    name = UnboundedCharField(blank=True)
    category = UnboundedCharField(blank=True)

    def __str__(self):
        return "%s (AF ID %s)" % (self.name, self.af_id)


class GroupMemberhip(models.Model):
    # Use memership values defined by Alumnforce
    MEMBERSHIP_ROLES = (
        ('banned', _('banned')),
        ('invited', _('invited')),
        ('member', _('member')),
        ('moderator', _('moderator')),
        ('onlist', _('on list')),
        ('responsible', _('responsible')),
        ('unsubscribed', _('unsubscribed')),
    )
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    role = models.SlugField(choices=MEMBERSHIP_ROLES)

    class Meta:
        unique_together = ('group', 'account')
