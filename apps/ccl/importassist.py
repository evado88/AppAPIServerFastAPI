
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
        # details
        {"id": "name", "name": "Name", "dataType": "text"},
        {"id": "description", "name": "Description", "dataType": "text"},
        # annual volume
        {"id": "annual_credit", "name": "Annual Credit", "dataType": "int"},
        {"id": "annual_nhima", "name": "Annual Nhima", "dataType": "int"},
        {"id": "annual_research", "name": "Annual Research", "dataType": "int"},
        {"id": "annual_walkins", "name": "Annual Walkins", "dataType": "int"},
        {"id": "annual_shift", "name": "Projected % Shift to Testing", "dataType": "int"},
        # lab plans
        {"id": "sites_no", "name": "Sites Performing Test", "dataType": "int"},
        {"id": "staff_no", "name": "Staff Performing Test", "dataType": "int"},
        # instrumeny usage
        {"id": "runs_day_week", "name": "No of Days Per Week Test is Run", "dataType": "int"},
        {"id": "runs_shift_day", "name": "No of Shifts Per Day Rest is Run", "dataType": "int"},
        # labor per sample
        {
            "id": "avg_hr_wage_analysis",
            "name": "Average Hourly Wage for Staff Performing Analysis",
            "dataType": "float",
        },
        {"id": "setup_min", "name": "Set Up (hands on min)", "dataType": "int"},
        {"id": "analysis_min", "name": "Analysis (hands on min)", "dataType": "int"},
        {
            "id": "result_review_min",
            "name": "Result Review (min)",
            "dataType": "int",
        },
        {"id": "result_doc_min", "name": "Result Documentation (min)", "dataType": "int"},
        {"id": "retention", "name": "Retention", "dataType": "float"},
        # labor per result
        {
            "id": "avg_hr_wage_report",
            "name": "Average Hourly Wage for Staff Producing Reports",
            "dataType": "float",
        },
        {"id": "result_entry_min", "name": "Result Entry (min)", "dataType": "int"},
        {
            "id": "report_preparation_min",
            "name": "Report Preparation (min)",
            "dataType": "int",
        },
        {
            "id": "report_distribution_min",
            "name": "Report Distribution (min)",
            "dataType": "int",
        },
    ]

# test price volume fields

testPriceVolumeFields = [
        {"id": "name", "name": "Name", "dataType": "text"},
        {"id": "description", "name": "Description", "dataType": "text"},
        {"id": "month_name", "name": "Month Name", "dataType": "text"},
        {"id": "year", "name": "Year", "dataType": "int"},
        {"id": "volume", "name": "Volume", "dataType": "int"},
        {"id": "price", "name": "Price USD", "dataType": "float"},
    ]


