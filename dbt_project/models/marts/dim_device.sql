-- dim_device.sql
-- Device type dimension table
-- Device categories based on voltage tolerance (from BOMB paper structure)

with device_types as (
    select distinct device_idx from {{ ref('stg_transistor_raw') }}
),

annotated as (
    select
        device_idx,
        {{ dbt_utils.generate_surrogate_key(['device_idx']) }} as device_key,

        -- Device voltage classifications (aligned with BOMB paper Fig 3/4 clustering)
        case device_idx
            when 0 then 'Low-Voltage Type 1'
            when 1 then 'High-Voltage Type 1'
            when 2 then 'High-Voltage Type 2'
            when 3 then 'Low-Voltage Type 2'
            else 'Unknown Device Type ' || cast(device_idx as varchar)
        end as device_label,

        case device_idx
            when 0 then 'LVT'
            when 1 then 'HVT'
            when 2 then 'HVT'
            when 3 then 'LVT'
            else 'NOM'
        end as device_voltage_class

    from device_types
)

select * from annotated
