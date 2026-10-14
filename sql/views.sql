CREATE OR REPLACE VIEW avg_temp_por_dispositivo AS
SELECT
    device_id,
    AVG(temperature) AS avg_temp
FROM temperature_readings
GROUP BY device_id;

CREATE OR REPLACE VIEW leituras_por_hora AS
SELECT
    EXTRACT(HOUR FROM noted_date)::INTEGER AS hora,
    COUNT(*) AS contagem
FROM temperature_readings
GROUP BY EXTRACT(HOUR FROM noted_date)
ORDER BY hora;

CREATE OR REPLACE VIEW temp_max_min_por_dia AS
SELECT
    CAST(noted_date AS DATE) AS data,
    MAX(temperature) AS temp_max,
    MIN(temperature) AS temp_min
FROM temperature_readings
GROUP BY CAST(noted_date AS DATE)
ORDER BY data;