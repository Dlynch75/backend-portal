# Project Documentation

**Admin Portal**

`Username: admin`
`Password: admin@123`

## Setup

Django Management Commands

**Migrations**

`python manage.py makemirations`
`python manage.py mirate`

**Run Server**

`python manage.py runserver`

**MAC Env Active**

`source venv/bin/activate`

**Requirement Freez**

`pip freeze > requirements.txt`

## Code Commit Format

- **feat**: Mainstream feature development
- **requirements**: Requirement updates
- **script**: Scripts other than the main application
- **migration**: Migration related commits
- **bug**: Bug fixes
- **docs**: Documentation updates
- **test**: Testing code
- **refactor**: Refactoring of already written code

## Add Packages Json Values for Offer field in Package Model

- Teacher Single: `{"allow_application": 1}` with PackType : "single_teacher"
- Teacher Bronze: `{"allow_application": 5}` with PackType : "bronze_teacher"
- Teacher Silver: `{"allow_application": 20}` with PackType : "silver_teacher"
- Teacher Gold: `{"allow_application": null}` with PackType : "gold_teacher"
- School Bronze: `{"allow_application": 1}` with PackType : "bronze_school"
- School Silver: `{"allow_application": 20}` with PackType : "silver_school"
- School Gold: `{"allow_application": null}` with PackType : "gold_school"
