#!/usr/bin/env python
"""Parse data from AlumnForce CSV exports, in order to import them"""
import csv


# Mapping from CSV columns to database fields
ALUMNFORCE_FIELDS = {
    'Identifiant AF': 'af_id',
    'Identifiant école': 'ax_id',
    'Prénom': 'firstname',
    'Nom d\'état civil': 'lastname',
    'Nom d\'usage': 'commonname',
    'Civilité' : 'civility',
    'Date de naissance': 'birthdate',
    'Adresse personnelle - Ligne 1': 'address_1',
    'Adresse personnelle - Ligne 2': 'address_2',
    'Adresse personnelle - Ligne 3': 'address_3',
    'Adresse personnelle - Ligne 4': 'address_4',
    'Adresse personnelle - Code Postal': 'address_postcode',
    'Adresse personnelle - Ville': 'address_city',
    'Adresse personnelle - État': 'address_state',
    'Adresse personnelle - Pays': 'address_country',
    'NPAI': 'address_npai',
    'Téléphone fixe personnel': 'phone_personnal',
    'Téléphone mobile personnel': 'phone_mobile',
    'Email personnel 1': 'email_1',
    'Email personnel 2': 'email_2',
    'Nationalité': 'nationality',
    'Décédé': 'dead',
    'Date de décès': 'deathdate',
    'Type d\'utilisateur': 'user_kind',
    'Rôles supplémentaires': 'additional_roles',
    'Login X.org': 'xorg_id',
    'Matricule école': 'school_id',
    'Voie d\'entrée': 'admission_path',
    'Domaine du cursus': 'cursus_domain',
    'Intitulé du cursus': 'cursus_name',
    'Corps actuel': 'corps_current',
    'Corps d\'origine': 'corps_origin',
    'Grade': 'corps_grade',
    'Surnom': 'nickname',
    'Seconde nationalité': 'nationality_2',
    'Troisième nationalité': 'nationality_3',
    'Mort pour la france': 'dead_for_france',
    'Sections sportive à l’X': 'sport_section',
    'Ex-binets': 'binets',
    'Réception courrier': 'mail_reception',
    'Inscription aux newsletters': 'newsletter_inscriptions',
    'URL de la photo de profil': 'profile_picture_url',
}


def import_csv(csv_file_path):
    with open(csv_file_path, 'r', encoding='utf-8') as csv_stream:
        reader = csv.reader(csv_stream, delimiter='\t', quotechar='"', escapechar='\\', strict=True)
        header_row = []
        for row in reader:
            if reader.line_num == 1:
                # Parse the header line
                for col_name in row:
                    # Use the ALUMNFORCE_FIELDS translation if it is known, otherwise the column name
                    header_row.append(ALUMNFORCE_FIELDS.get(col_name, col_name))

                # Sanity check
                assert len(set(header_row)) == len(header_row), "There are columns which are not unique in {}".format(csv_file_path)
                continue

            assert len(row) == len(header_row), "The CSV line {} has a different length from the header".format(reader.line_num)
            print(list(zip(header_row, row)))
