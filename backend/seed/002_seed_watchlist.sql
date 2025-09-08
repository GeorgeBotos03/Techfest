INSERT INTO watchlist(iban, label, risk_level) VALUES
('RO49AAAA1B31007593840000','Confirmed mule',95)
ON CONFLICT (iban) DO NOTHING;
