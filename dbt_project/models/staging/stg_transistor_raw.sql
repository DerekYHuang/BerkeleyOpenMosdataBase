-- stg_transistor_raw.sql
-- Staging model: casts and renames raw BOMB transistor characterization data
-- Source: bomb_transistor_flat.parquet loaded into S3 / Redshift

with raw as (
    select * from {{ ref('load_parquet') }}
),

staged as (
    select
        -- Dimension keys
        cast(montecarlo_idx   as integer)   as montecarlo_idx,
        cast(temperature_c    as integer)   as temperature_c,
        cast(process_idx      as integer)   as process_idx,
        cast(device_idx       as integer)   as device_idx,

        -- Voltage sweep steps
        cast(vbs_step         as integer)   as vbs_step,
        cast(vgs_step         as integer)   as vgs_step,
        cast(vds_step         as integer)   as vds_step,

        -- Electrical parameters
        cast(ibias            as float)     as ibias,
        cast(y11              as float)     as y11,
        cast(y12              as float)     as y12,
        cast(y13              as float)     as y13,
        cast(y21              as float)     as y21,
        cast(y22              as float)     as y22,
        cast(y23              as float)     as y23,
        cast(y31              as float)     as y31,
        cast(y32              as float)     as y32,
        cast(y33              as float)     as y33,

        -- Derived flags
        cast(thermal_stress_flag as integer) as thermal_stress_flag,

        -- Surrogate key for fact table
        {{ dbt_utils.generate_surrogate_key([
            'montecarlo_idx', 'temperature_c', 'process_idx', 'device_idx',
            'vbs_step', 'vgs_step', 'vds_step'
        ]) }} as characterization_id

    from raw
    where ibias is not null
)

select * from staged
