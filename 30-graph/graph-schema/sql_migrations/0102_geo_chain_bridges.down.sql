DELETE FROM edge_classified_as WHERE system = 'iso3166_iso4217';

DELETE FROM edge_classified_as WHERE system = 'iso4217_sovereign';

DELETE FROM edge_classified_as WHERE system = 'sovereign_iso4217';

DELETE FROM edge_classified_as WHERE system = 'locode_sovereign';

DELETE FROM edge_classified_as WHERE system = 'sovereign_locode';
