###### Aufruf über: #######
# python manage.py dbshell
# Dann das SQL oben reinkopieren und mit Enter bestätigen.
######

-- 1. Eine Person anlegen (Funktionierte bereits, aber zur Sicherheit falls du neu startest)
-- Falls ID 1 schon existiert, wird dieser Befehl übersprungen oder wirft einen Fehler, das ist ok.
INSERT INTO crm_person (id, salutation, title, first_name, last_name, birth_date, pref_lang)
VALUES (1, 'HERR', 'Dr.', 'Max', 'Mustermann', '1980-05-15', 'DE')
ON CONFLICT (id) DO NOTHING;

-- 2. Die Legal Entity anlegen (Die Firma)
INSERT INTO crm_legalentity (id, entity_type, internal_id, company_name, vat_id, tax_id_local, tax_regime, is_zec_approved, webseite, parent_id, is_private_person_id)
VALUES (1, 'COMPANY', 'KD-260001', 'Musterfirma GmbH', 'DE123456789', '99/123/45678', 'REGULAR', FALSE, 'https://www.musterfirma.de', NULL, NULL);

-- 3. Postanschrift für die Firma
INSERT INTO crm_postaladdress (legal_entity_id, address_type, street, street_extra, zip_code, city, province, country)
VALUES (1, 'BILLING', 'Musterstraße 42', 'Hinterhaus, 2. OG', '10115', 'Berlin', 'Berlin', 'Germany');

-- 4. Die Person als offiziellen Kontakt zuweisen
INSERT INTO crm_contactperson (legal_entity_id, person_id, employment_type, department, is_allgemein, is_re_contact, is_ls_contact, is_as_contact, is_vertrag)
VALUES (1, 1, 'INTERNAL', 'Geschäftsführung', TRUE, TRUE, FALSE, TRUE, TRUE);

-- 5. Kommunikationskanäle
INSERT INTO crm_commchannel (person_id, entity_id, channel_type, value, label, is_primary)
VALUES (1, NULL, 'MAIL', 'max@musterfirma.de', 'Geschäftlich', TRUE);

INSERT INTO crm_commchannel (person_id, entity_id, channel_type, value, label, is_primary)
VALUES (1, NULL, 'PHONE', '+49 30 12345678', 'Zentrale', FALSE);

-- 6. Eine erste Interaktion
-- Hinweis: Falls dein User nicht ID 1 hat, hier die ID deines Admin-Accounts eintragen
INSERT INTO crm_interaction (entity_id, person_id, interaction_type, subject, content, created_at, created_by_id)
VALUES (1, 1, 'MEETING', 'Erstgespräch Kooperation', 'Kunde hat großes Interesse an IT-Strategieberatung bekundet.', CURRENT_TIMESTAMP, 1);

-- Sub-Unternehmer anlegen (Parent-ID ist 1, die Musterfirma GmbH)
INSERT INTO crm_legalentity (id, entity_type, internal_id, company_name, vat_id, tax_id_local, tax_regime, is_zec_approved, webseite, parent_id, is_private_person_id)
VALUES (2, 'COMPANY', 'KD-260002', 'Muster-IT Service GmbH', 'DE987654321', '88/111/22222', 'REGULAR', FALSE, 'https://it-service.de', 1, NULL);

-- Adresse für den Sub-Unternehmer
INSERT INTO crm_postaladdress (legal_entity_id, address_type, street, street_extra, zip_code, city, province, country)
VALUES (2, 'BRANCH', 'Technikpark 1', 'Gebäude B', '80331', 'München', 'Bayern', 'Germany');

-- Schritt A: Alte (fehlerhafte) Verknüpfungen löschen, um sauber zu starten
DELETE FROM crm_contactperson WHERE person_id IN (2, 3);
DELETE FROM crm_commchannel WHERE person_id IN (2, 3);

-- Schritt B: Sabine (ID 2) der Musterfirma (ID 1) als Einkäuferin zuweisen
INSERT INTO crm_contactperson (legal_entity_id, person_id, employment_type, department, is_allgemein, is_re_contact, is_ls_contact, is_as_contact, is_vertrag)
VALUES (1, 2, 'INTERNAL', 'Einkauf', FALSE, TRUE, FALSE, TRUE, FALSE);

-- Schritt C: Kevin (ID 3) der Musterfirma (ID 1) als IT-Admin zuweisen
INSERT INTO crm_contactperson (legal_entity_id, person_id, employment_type, department, is_allgemein, is_re_contact, is_ls_contact, is_as_contact, is_vertrag)
VALUES (1, 3, 'INTERNAL', 'IT-Betrieb', FALSE, FALSE, FALSE, TRUE, FALSE);

-- Schritt D: Kommunikationskanäle für beide (damit sie erreichbar sind)
INSERT INTO crm_commchannel (person_id, entity_id, channel_type, value, label, is_primary)
VALUES (2, NULL, 'MAIL', 'einkauf@musterfirma.de', 'Direkt', TRUE);

INSERT INTO crm_commchannel (person_id, entity_id, channel_type, value, label, is_primary)
VALUES (3, NULL, 'MAIL', 'support@musterfirma.de', 'Support', TRUE);