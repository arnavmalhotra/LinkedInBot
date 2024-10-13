from linkedin_api import Linkedin
linkedin = Linkedin('Arnav44malhotra@gmail.com', 'IGotHacked@1628.com')
print(linkedin.search_people(keywords='Software Engineering Toronto',limit=10,regions="urn:li:geo:12345"))
#print(linkedin.get_profile(urn_id='ACoAAEbUakgBfWNeYAyrUlkljweSaIJfz009flQ'))