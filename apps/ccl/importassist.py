
# labs

labFields = [
        {"id": "name", "name": "Name", "dataType": "text"},
        {"id": "description", "name": "Description", "dataType": "text"},
    ]

# reagents and consumables

reagentFields = [
        {"id": "name", "name": "Name", "dataType": "text"},
        {"id": "description", "name": "Description", "dataType": "text"},
        {"id": "cost", "name": "Cost", "dataType": "float"},
        {"id": "expiry_period", "name": "Expiry Period", "dataType": "int"},
        {
            "id": "generic_reagent_unit",
            "name": "Generic Reagent Unit",
            "dataType": "text",
        },
        {"id": "quantity_per_gru", "name": "Quantity Per GRU", "dataType": "int"},
        {"id": "tests_per_gru", "name": "Tests Per GRU", "dataType": "int"},
    ]

# instruments

instrumentFields = [
        {"id": "name", "name": "Name", "dataType": "text"},
        {"id": "description", "name": "Description", "dataType": "text"},
        {"id": "serial_no", "name": "Serial No", "dataType": "text"},
        {"id": "cost", "name": "Cost", "dataType": "float"},
        {
            "id": "amortization",
            "name": "Amortization",
            "dataType": "int",
        },
        {"id": "maintenance_cost", "name": "Maintenance Cost", "dataType": "float"},
        {"id": "calibration_cycle", "name": "Calibrations Per Year", "dataType": "int"},
        {
            "id": "calibration_kit_cost",
            "name": "Calibration Kit Cost",
            "dataType": "float",
        },
        {
            "id": "calibration_service_cost",
            "name": "Calibration Service Cost",
            "dataType": "float",
        },
]

# tests
testFields = [
        {"id": "name", "name": "Name", "dataType": "text"},
        {"id": "description", "name": "Description", "dataType": "text"},
        {"id": "lab_id", "name": "Lab", "dataType": "int"},
        {"id": "cost", "name": "Cost", "dataType": "float"},
        {
            "id": "amortization",
            "name": "Amortization",
            "dataType": "t",
        },
        {"id": "annual_cost", "name": "Annual Cost", "dataType": "float"},
        {"id": "maintenance_cost", "name": "Maintenance Cost", "dataType": "float"},
        {"id": "calibration_cycle", "name": "Calibration Cycle", "dataType": "float"},
        {
            "id": "calibration_kit_cost",
            "name": "Calibration Kit Cost",
            "dataType": "float",
        },
        {
            "id": "calibration_service_cost",
            "name": "Calibration Service Cost",
            "dataType": "float",
        },
        {"id": "annual_credit", "name": "Annual Credit", "dataType": "int"},
        {"id": "annual_nhima", "name": "Annual Nhima", "dataType": "int"},
        {"id": "annual_research", "name": "Annual Research", "dataType": "int"},
        {"id": "annual_walkins", "name": "Annual Walkins", "dataType": "int"},
        {"id": "annual_shift", "name": "Annual Shift", "dataType": "int"},
        {"id": "annual_total", "name": "Annual Total", "dataType": "int"},
        {"id": "sites_no", "name": "Sites No", "dataType": "int"},
        {"id": "staff_no", "name": "Staff No", "dataType": "int"},
        {"id": "runs_day_week", "name": "Runs Day Week", "dataType": "int"},
        {"id": "runs_shift_day", "name": "Runs Shift Day", "dataType": "int"},
        {"id": "runs_annual", "name": "Runs Annual", "dataType": "int"},
        {
            "id": "runs_average_volume",
            "name": "Runs Average Volume",
            "dataType": "float",
        },
        {
            "id": "avg_hr_wage_analysis",
            "name": "Avg Hr Wage Analysis",
            "dataType": "float",
        },
        {"id": "setup_min", "name": "Setup Min", "dataType": "int"},
        {"id": "analysis_min", "name": "Analysis Min", "dataType": "int"},
        {
            "id": "result_review_min",
            "name": "Result Review Min",
            "dataType": "int",
        },
        {"id": "result_doc_min", "name": "Result Doc Min", "dataType": "int"},
        {"id": "retention", "name": "Retention", "dataType": "float"},
        {
            "id": "total_labor_analysis_min",
            "name": "Total Labor Analysis Min",
            "dataType": "float",
        },
        {
            "id": "total_labor_analysis_year",
            "name": "Total Labor Analysis Year",
            "dataType": "float",
        },
        {
            "id": "avg_hr_wage_report",
            "name": "Avg Hr Wage Report",
            "dataType": "float",
        },
        {"id": "result_entry_min", "name": "Result Entry Min", "dataType": "int"},
        {
            "id": "report_preparation_min",
            "name": "Report Preparation Min",
            "dataType": "int",
        },
        {
            "id": "report_distribution_min",
            "name": "Report Distribution Min",
            "dataType": "int",
        },
        {
            "id": "total_labor_result_min",
            "name": "Total Labor Result Min",
            "dataType": "int",
        },
        {
            "id": "total_labor_result_year",
            "name": "Total Labor Result Year",
            "dataType": "float",
        },
        {"id": "reagent_list", "name": "Reagents", "dataType": "list"},
        {"id": "instrument_list", "name": "Instruments", "dataType": "list"},
    ]

# test price volume fields

testPriceVolumeFields = [
        {"id": "name", "name": "Name", "dataType": "text"},
        {"id": "description", "name": "Description", "dataType": "text"},
        {"id": "month", "name": "Month", "dataType": "text"},
        {"id": "year", "name": "Year", "dataType": "int"},
        {"id": "price_usd", "name": "Price USD", "dataType": "int"},
        {"id": "volume", "name": "Volume", "dataType": "int"},
    ]


