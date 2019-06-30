from django.core.validators import validate_comma_separated_integer_list
from django.db import models
from django.utils.translation import ugettext_lazy as _

from xorgdata.utils.fields import DottedSlugField, UnboundedCharField


class Account(models.Model):
    # User kinds defined by the AX
    KIND_GRADUATED = 1
    KIND_EMPLOYEE = 3
    KIND_STUDENT = 5
    KIND_VISITOR = 7
    KIND_ASSOCIATED_MEMBER = 9
    KIND_WIDOW = 10
    KINDS = {
        KIND_GRADUATED: "Diplômé(e)",
        KIND_EMPLOYEE: "Personnel de l'AX",
        KIND_STUDENT: "Élève/Étudiant(e)",
        KIND_VISITOR: "Visiteur",
        KIND_ASSOCIATED_MEMBER: "Membre associé",
        KIND_WIDOW: "Veuves/Veufs",
    }
    # Roles defined by the AX
    ROLE_GUEST = 1
    ROLE_SUPER_ADMIN = 2
    ROLE_TOTAL_ADMIN = 3
    ROLE_GRADUATED = 4
    ROLE_CONTRIBUTOR = 5
    ROLE_STUDENT = 7
    ROLE_SUBSCRIBED = 17
    ROLE_ASSOCIATED_MEMBER = 19
    ROLE_CONTENT_ADMIN = 21
    ROLE_ACCOUNTING_ADMIN = 22
    ROLE_WIDOW = 26
    ROLES = {
        ROLE_GUEST: "Visiteur",
        ROLE_SUPER_ADMIN: "Super-administrateur",
        ROLE_TOTAL_ADMIN: "Administrateur total",
        ROLE_GRADUATED: "Diplômé",
        ROLE_CONTRIBUTOR: "Cotisant",
        ROLE_STUDENT: "Élève et étudiant",
        ROLE_SUBSCRIBED: "Abonné",
        ROLE_ASSOCIATED_MEMBER: "Membre associé",
        ROLE_CONTENT_ADMIN: "Administrateur contenu",
        ROLE_ACCOUNTING_ADMIN: "Administrateur comptable",
        ROLE_WIDOW: "Veuves/Veufs",
    }

    af_id = models.IntegerField(primary_key=True)
    ax_id = models.CharField(max_length=20, blank=True, null=True)
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
    additional_roles = UnboundedCharField(blank=True,
                                          validators=[validate_comma_separated_integer_list])
    xorg_id = DottedSlugField(max_length=255, blank=True, null=True)
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
    last_update = models.DateField()
    deleted_since = models.DateField(blank=True, null=True)

    def __str__(self):
        """Get a string identifying an account"""
        # Start by the X.org ID or names or email
        if self.xorg_id:
            result = self.xorg_id
        elif self.first_name and self.last_name:
            result = '{} {}'.format(self.first_name, self.last_name)
        elif self.email_1:
            result = self.email_1
        else:
            result = '?'

        # Add the AX ID or the AF ID
        if self.ax_id:
            result += ' (AX ID {})'.format(self.ax_id)
        else:
            result += ' (AF ID {})'.format(self.af_id)
        return result

    def get_additional_roles(self):
        """Return the additional roles as a list of integers"""
        if not self.additional_roles:
            return []
        return [int(r) for r in self.additional_roles.split(',')]

    @property
    def alumnforce_profile_url(self):
        """URL on AlumnForce website"""
        return 'https://ax.polytechnique.org/person/by-id/{:d}'.format(self.af_id)


class AcademicInformation(models.Model):
    account = models.ForeignKey('Account', related_name='degrees', on_delete=models.CASCADE)
    diploma_reference = UnboundedCharField()
    diplomed = models.NullBooleanField()
    diplomation_date = models.DateField(blank=True, null=True)
    cycle = UnboundedCharField(blank=True)
    domain = UnboundedCharField(blank=True)
    name = UnboundedCharField(blank=True)
    last_update = models.DateField()


class ProfessionnalInformation(models.Model):
    account = models.ForeignKey('Account', related_name='jobs', on_delete=models.CASCADE)
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
    last_update = models.DateField()


class Group(models.Model):
    af_id = models.IntegerField(primary_key=True)
    ax_id = models.CharField(max_length=20, blank=True, null=True, unique=True)
    url = UnboundedCharField(blank=True)
    name = UnboundedCharField(blank=True)
    category = UnboundedCharField(blank=True)
    last_update = models.DateField()

    def __str__(self):
        return "%s (AF ID %s)" % (self.name, self.af_id)


class GroupMembership(models.Model):
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
    # Roles that really mean that the user belongs to the group
    IN_GROUP_ROLES = frozenset(('member', 'moderator', 'onlist', 'responsible'))
    account = models.ForeignKey(Account, related_name='group_memberships', on_delete=models.CASCADE)
    group = models.ForeignKey(Group, related_name='memberships', on_delete=models.CASCADE)
    role = models.SlugField(choices=MEMBERSHIP_ROLES)
    last_update = models.DateField()

    class Meta:
        unique_together = ('group', 'account')


class ImportLog(models.Model):
    # Kind of export file. Order is important as it determines the order used to
    # parse incoming export files: users need to be first created, then groups,
    # then everything else (that depends on users and/or groups).
    KNOWN_EXPORT_KINDS = (
        ('users', _('users')),
        ('groups', _('groups')),
        ('groupmembers', _('groupmembers')),
        ('userdegrees', _('userdegrees')),
        ('userjobs', _('userjobs')),
    )
    # Error code when importing data
    SUCCESS = 0
    ALUMNFORCE_ERROR = 1
    XORG_ERROR = 2
    ERROR_CODES = (
        (SUCCESS, _('success')),
        (ALUMNFORCE_ERROR, _('AlumnForce error')),
        (XORG_ERROR, _('X.org error')),
    )
    date = models.DateField()
    export_kind = models.SlugField(choices=KNOWN_EXPORT_KINDS)
    is_incremental = models.BooleanField()
    error = models.IntegerField(choices=ERROR_CODES)
    num_modified = models.IntegerField(null=True, blank=True)
    message = UnboundedCharField(blank=True)


class ExportLog(models.Model):
    KIND_AUTH = 'auth'
    KNOWN_KINDS = (
        (KIND_AUTH, _('X.org auth')),
    )
    SUCCESS = 0
    ERROR_CODES = (
        (SUCCESS, _('success')),
    )
    date = models.DateField()
    export_kind = models.SlugField(choices=KNOWN_KINDS)
    error = models.IntegerField(choices=ERROR_CODES)
    num_items = models.IntegerField(null=True, blank=True)
    message = UnboundedCharField(blank=True)
