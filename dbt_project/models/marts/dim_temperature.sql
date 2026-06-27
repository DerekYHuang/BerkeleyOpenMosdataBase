-- dim_temperature.sql
-- Temperature dimension with thermal threshold flags

with temp_values as (
    select distinct temperature_c from {{ ref('stg_transistor_raw') }}
),

annotated as (
    select
        temperature_c,
        {{ dbt_utils.generate_surrogate_key(['temperature_c']) }} as temperature_key,

        case
            when temperature_c < 0  then 'Sub-Zero'
            when temperature_c < 50 then 'Ambient'
            when temperature_c < 100 then 'Elevated'
            else 'High-Stress'
        end as thermal_regime,

        -- Flag high-stress temperatures (≥120°C) as defined in BOMB paper
        case when temperature_c >= 120 then true else false end as is_high_stress,

        -- Flag operating range (typical industrial: -20°C to 85°C)
        case
            when temperature_c between -20 and 85 then true
            else false
        end as within_industrial_range

    from temp_values
)

select * from annotated
