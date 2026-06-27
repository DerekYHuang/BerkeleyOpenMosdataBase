-- fact_transistor_characterization.sql
-- Core fact table: one row per transistor measurement across all sweep dimensions
-- Grain: montecarlo × temperature × process × device × Vbs × Vgs × Vds

with staged as (
    select * from {{ ref('stg_transistor_raw') }}
),

dim_device as (
    select * from {{ ref('dim_device') }}
),

dim_process_corner as (
    select * from {{ ref('dim_process_corner') }}
),

dim_temperature as (
    select * from {{ ref('dim_temperature') }}
),

final as (
    select
        s.characterization_id,

        -- Foreign keys to dimensions
        d.device_key,
        p.process_key,
        t.temperature_key,

        -- Measurement context
        s.montecarlo_idx,
        s.vbs_step,
        s.vgs_step,
        s.vds_step,

        -- Electrical measurements
        s.ibias,
        s.y11,
        s.y12,
        s.y13,
        s.y21,
        s.y22,
        s.y23,
        s.y31,
        s.y32,
        s.y33,

        -- Thermal stress flag (key analytical dimension)
        s.thermal_stress_flag,

        -- Derived: ibias absolute magnitude (useful for stability analysis)
        abs(s.ibias) as ibias_abs,

        -- Derived: transconductance proxy (y21 is the forward transconductance)
        s.y21 as gm_proxy

    from staged s
    left join dim_device d
        on s.device_idx = d.device_idx
    left join dim_process_corner p
        on s.process_idx = p.process_idx
    left join dim_temperature t
        on s.temperature_c = t.temperature_c
)

select * from final
