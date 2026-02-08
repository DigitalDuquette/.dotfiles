-- MacBook age calculator
-- Tracks hardware refresh cycles

--#region Setup dates
CREATE TEMP TABLE mac_dates (
    intel_mac DATE,
    arm_mac DATE,
    m2_air DATE
);

INSERT INTO mac_dates (intel_mac, arm_mac, m2_air)
VALUES (
    '2019-01-16',  -- date received first work macbook pro
    '2021-11-29',  -- date received first apple silicon macbook pro m1
    '2024-02-14'   -- date received first apple silicon macbook air m2
);
--#endregion

--#region Calculate ages
SELECT
    -- Intel Mac lifespan (until replaced)
    date_diff('day', intel_mac, arm_mac) AS intel_mac_days_old,
    date_diff('month', intel_mac, arm_mac) AS intel_mac_months_old,
    ROUND(date_diff('day', intel_mac, arm_mac) / 365.0, 2) AS intel_mac_years_old,

    -- M1 Mac current age
    date_diff('day', arm_mac, current_date) AS arm_mac_days_old,
    date_diff('month', arm_mac, current_date) AS arm_mac_months_old,
    ROUND(date_diff('day', arm_mac, current_date) / 365.0, 2) AS arm_mac_years_old,

    -- M2 Air current age
    date_diff('day', m2_air, current_date) AS m2_air_days_old,
    date_diff('month', m2_air, current_date) AS m2_air_months_old,
    ROUND(date_diff('day', m2_air, current_date) / 365.0, 2) AS m2_air_years_old
FROM mac_dates;
--#endregion

--#region Cleanup
DROP TABLE mac_dates;
--#endregion
