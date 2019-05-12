#!/usr/bin/env python3
"""Handle the CSV files that AlumnForce's website (ax.polytechnique.org) handles

The website can export ISO-8859-15 CSV files and import UTF-8 CSV files.
"""


class BoolType(object):
    """A boolean in AlumnForce CSV"""
    @staticmethod
    def encode(value):
        if value is None:
            return ''
        return '1' if value else '0'

    @staticmethod
    def decode(value):
        if value == '0':
            return False
        elif value == '1':
            return True
        elif value == '':
            return None
        raise ValueError()


class YesNoBoolType(object):
    """A boolean in AlumnForce CSV encoded as "Oui" and "Non" """
    @staticmethod
    def encode(value):
        if value is None:
            return ''
        return 'Oui' if value else 'Non'

    @staticmethod
    def decode(value):
        if value == 'Non':
            return False
        elif value == 'Oui':
            return True
        elif value == '':
            return None
        raise ValueError()


class CommaListType(object):
    """A list of values separated by commas"""
    @staticmethod
    def encode(value):
        if not value:
            return ''
        return ','.join(value)

    @staticmethod
    def decode(value):
        if not value:
            return None
        return value.split(',')


class CommaSpaceListType(object):
    """A list of values separated by commas"""
    @staticmethod
    def encode(value):
        if not value:
            return ''
        return ', '.join(value)

    @staticmethod
    def decode(value):
        if not value:
            return None
        return value.split(', ')


# CSV and JSON field names with the data type ("None" type is unicode string)
# Use "." for sub-object fields in JSON
ALUMNFORCE_FIELDS = (
    ('Identifiant (AlumnForce)', 'id_af', None),
    ('Identifiant (École)', 'id_ax', None),
    ('Prénom', 'first_name', None),
    ('Nom d\'état-civil', 'last_name', None),
    ('Nom d\'usage', 'usage_name', None),
    ('Civilité (Mme / Mlle / M.)', 'civility', None),
    ('Date de naissance', 'birth_date', None),
    ('Adresse personnelle - Ligne 1', 'personal.address.line_1', None),
    ('Adresse personnelle - Ligne 2', 'personal.address.line_2', None),
    ('Adresse personnelle - Ligne 3', 'personal.address.line_3', None),
    ('Adresse personnelle - Ligne 4', 'personal.address.line_4', None),
    ('Adresse personnelle - Région', 'personal.address.region', None),
    ('Adresse personnelle - Ville', 'personal.address.city', None),
    ('Adresse personnelle - État', 'personal.address.state', None),
    ('Adresse personnelle - Code postal', 'personal.address.code', None),
    ('Adresse personnelle - Cedex', 'personal.address.cedex', None),
    ('Adresse personnelle - Pays (ISO)', 'personal.address.country', None),
    ('Adresse personnelle - NPAI (Oui [1] / Non [0])', 'personal.address.bounced', BoolType),
    ('Téléphone fixe personnel', 'personal.fix_phone', None),
    ('Téléphone mobile personnel', 'personal.cell_phone', None),
    ('Email personnel 1', 'email.personal_1', None),
    ('Email personnel 2', 'email.personal_2', None),
    ('Nationalité', 'nationality', None),
    ('Situation matrimoniale', 'marital_status', None),
    ('Membre décédé (Oui [1] / Non [0])', 'is_dead', BoolType),
    ("Statut (Non enregistré [0] / En cours d'activation [1] / Compte bloqué [2] / Compte activé [3] / Clé d'activation envoyée [4] / En attente de validation [5] / Ne souhaite pas activer son compte [6] / Compte expiré [8])", 'account_status', None),  # noqa
    ('Compte activé (Oui [1] / Non [0])', 'is_activated', BoolType),
    ("Type utilisateur (Diplômé(e) [1] / Personnel de l'association [3] / Élève / étudiant(e) [5] / Visiteur [7] / Membre associé [9] / Veuves/Veufs [10])", 'user_kind', None),  # noqa
    ('Rôle supplémentaire (Visiteur [1] / Administrateur total [3] / Diplômé [4] / Cotisant [5] / Élève et étudiant [7] / Abonné [17] / Membre associé [19] / Administrateur contenu [21] / Administrateur comptable [22] / Veuves/Veufs [26])', 'roles', CommaListType),  # noqa
    ('Forcer le statut de cotisant (Oui [1] / Non [0])', 'force_contributor', BoolType),
    ('Référence du diplôme', 'school.degree_ref', None),
    ('Ecole', 'school.name', None),
    ('Filière (L/M/D)', 'school.stream', None),
    ('Spécialisation', 'speciality', None),
    ('Parcours', 'curriculum', None),
    ("Niveau d'étude / Nombre d'années post bac", 'study_level', None),
    ('Mode', 'mode', None),
    ('A obtenu son diplôme ? (Oui [1] / Non [0])', 'school.has_graduated', BoolType),
    ('Date de promotion', 'school.graduation_date', None),
    ("Date d'intégration", 'school.entry_date', None),
    ('Publier données académiques', 'school.publish_academic', BoolType),
    ('Situation actuelle', 'work.current_situation', None),
    ('Poste actuel', 'work.current_job', None),
    ('Code Fontion / Métier', 'work.job_code', None),
    ('Fonction / Métier', 'work.function', None),
    ('Niveau du poste', 'work.job_level', None),
    ('Entreprise - Nom', 'work.company.name', None),
    ("Entreprise - Secteur d'activité", 'work.company.sector', None),
    ('Entreprise - Code SIRET', 'work.company.siret', None),
    ('Entreprise - Site internet', 'work.company.website', None),
    ('Adresse professionnelle - Ligne 1', 'work.company.address.line_1', None),
    ('Adresse professionnelle - Ligne 2', 'work.company.address.line_2', None),
    ('Adresse professionnelle - Ligne 3', 'work.company.address.line_3', None),
    ('Adresse professionnelle - Ligne 4', 'work.company.address.line_4', None),
    ('Adresse professionnelle - Région', 'work.company.address.region', None),
    ('Adresse professionnelle - Ville', 'work.company.address.city', None),
    ('Adresse professionnelle - État', 'work.company.address.country', None),
    ('Adresse professionnelle - Code postal', 'work.company.address.code', None),
    ('Adresse professionnelle - Cedex', 'work.company.address.cedex', None),
    ('Adresse professionnelle - Pays (ISO)', 'work.company.address.iso', None),
    ('Téléphone fixe professionnel', 'work.company.fix_phone', None),
    ('Téléphone mobile professionnel', 'work.company.cell_phone', None),
    ('Fax professionnel', 'work.company.fax', None),
    ('Email professionnel', 'email.professional', None),
    ("Début de l'expérience", 'work.company.begin', None),
    ("Fin de l'expérience", 'work.company.end', None),
    ('Type de contrat', 'work.company.contract_kind', None),
    ('Salaire réel', 'work.company.wage', None),
    ('Tranche de salaire', 'work.company.wage_bracket', None),
    ("Je souhaite contribuer à la vie de l'Association: CA, Colloque, PDX, Bal de l'X, Grand Magnan ... (Oui [1] / Non [0])", 'wish.ax', BoolType),  # noqa
    ('Je suis prêt à aider des camarades en transition professionnelle, ou porteurs de projet (Oui [1] / Non [0])', 'wish.help', BoolType),  # noqa
    ('Je suis intéressé par les programmes de parrainage et de mentoring (Oui [1] / Non [0])', 'wish.mentoring', BoolType),  # noqa
    ('Je suis prêt à donner un peu de temps pour aider des camarades, ou familles de camarades, en difficulté via la Caisse de Solidarité (Oui [1] / Non [0])', 'wish.solidarity', BoolType),  # noqa
    ("J'accepte de recevoir les mails de l'Association (Oui [1] / Non [0])", 'wish.ax_emails', BoolType),
    ("Je peux intervenir lors d'événements, pour animer un atelier, participer à une table ronde ou donner une conférence (Oui [1] / Non [0])", 'wish.animate', BoolType),  # noqa
    ("J'accepte de figurer dans l'annuaire papier (Oui [1] / Non [0])", 'wish.in_directory', BoolType),
    ("Je souhaite recevoir l'annuaire papier (Oui [1] / Non [0])", 'wish.receive_directory', BoolType),
    ("Email d'identification", 'email.identification', None),
    ('Email de notification', 'email.notification', None),
    ('Dernière mise à jour', 'last_update', None),
    ('Dernière connexion', 'last_login', None),
    ('Langues', 'languages', CommaSpaceListType),
    ("Entreprise - A crée l'entreprise ? (Oui [1] / Non [0])", 'work.company.is_founder', BoolType),
    ("Entreprise - A repris l'entreprise ? (Oui [1] / Non [0])", 'work.company.is_taker', BoolType),
    ('Statut cotisant? (Oui [1] / Non [0])', 'is_contributing', BoolType),
    ('Fidélité cotisant (nombre étoiles)', 'contribution_fidelity', None),
    ('Délégué de promotion', 'is_delegate', BoolType),
    ('Date de décès', 'death_date', None),
    ('Adresse secondaire - Ligne 1', 'personal.address2.line_1', None),
    ('Adresse secondaire - Ligne 2', 'personal.address2.line_2', None),
    ('Adresse secondaire - Ligne 3', 'personal.address2.line_3', None),
    ('Adresse secondaire - Ligne 4', 'personal.address2.line_4', None),
    ('Adresse secondaire - Région', 'personal.address2.region', None),
    ('Adresse secondaire - Ville', 'personal.address2.contry', None),
    ('Adresse secondaire - État', 'personal.address2.state', None),
    ('Adresse secondaire - Code postal', 'personal.address2.code', None),
    ('Adresse secondaire - Cedex', 'personal.address2.cedex', None),
    ('Adresse secondaire - Pays (ISO)', 'personal.address2.iso', None),
    ('Téléphone fixe secondaire', 'personal.fix_phone_2', None),
    ('Téléphone mobile secondaire', 'personal.cell_phone_2', None),
    ('Compte X.org actif', 'xorg.is_active', YesNoBoolType),
    ('Login X.org', 'xorg.login', None),
    ('Matricule École', 'school.id', None),
    ("Voie d'entrée", 'school.input', None),
    ('Domaine du cursus', 'school.domain', None),
    ('Intitulé du cursus', 'school.curriculum', None),
    ('Corps actuel', 'corps.current', None),
    ("Corps d'origine", 'corps.original', None),
    ('Grade', 'corps.grade', None),
    ('Surnom', 'nickname', None),
    ('Seconde nationalité', 'nationality_2', None),
    ('Troisième nationalité', 'nationality_3', None),
    ('Mort pour la France', 'dead_for_france', None),
    ("Section sportive à l'X", 'school.sport', None),
    ('Ex-binets', 'school.binets', CommaListType),
    ('Réception courrier', 'has_postal_mail', None),
    ('Inscription aux newsletters', 'newsletters', CommaListType),
    ('Référent', 'referrer.is', None),
    ('Secteurs référent', 'referrer.sectors', None),
    ('Commentaire référent', 'referrer.comment', None),
    ('Info sup : commentaires divers', 'comments', None),
    ('Url d\'appel à cotisation', 'url_contribution', None),
)
