import AddIcon from '@mui/icons-material/Add';
import CancelIcon from '@mui/icons-material/Close';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import SaveIcon from '@mui/icons-material/Save';
import Box from '@mui/material/Box';
import Button from "@mui/material/Button";
import FormHelperText from '@mui/material/FormHelperText';
import Typography from "@mui/material/Typography";
import type {
    GridColDef,
    GridEventListener,
    GridRowId,
    GridRowModel,
    GridRowModesModel,
    GridRowsProp,
    GridSlotProps,
} from '@mui/x-data-grid';
import {
    DataGrid,
    GridActionsCellItem,
    GridRowModes,
    Toolbar,
} from '@mui/x-data-grid';
import React from 'react';
import { useController, type ValidateResult } from 'react-hook-form';
import { v6 as uuidv6 } from 'uuid';
import { type PrimitiveType, Question } from '../../context/FormTypes';

// Declare custom props to pass to the footer component
// See https://mui.com/x/api/data-grid/data-grid/#data-grid-prop-slotProps
declare module '@mui/x-data-grid' {
    interface FooterPropsOverrides {
        setRows: (newRows: (oldRows: GridRowsProp) => GridRowsProp) => void;
        setRowModesModel: (
            newModel: (oldModel: GridRowModesModel) => GridRowModesModel,
        ) => void;
        emptyRow: { [key: string]: PrimitiveType };
    }
}

export function GridInput({
    question,
}: {
    question: Readonly<Question>,
}) {
    const { field, fieldState } = useController({
        name: question.id,
        defaultValue: getInitialRows(question),
        rules: {
            validate: (): ValidateResult => {
                return Array.isArray(rows) && rows.length > 0
                    ? true
                    : "At least one record must be provided.";
            }
        },
    })

    // Populate rows with state from the form controller
    const [rows, _setRows] = React.useState<GridRowsProp>(field.value);

    // Attach the react-hook-form `onChange()` update to keep it in sync
    const setRows = (newRows: React.SetStateAction<GridRowsProp>) => {
        // Support both function and value for setState
        const value = typeof newRows === "function"
            ? (newRows as (prev: GridRowsProp) => GridRowsProp)(rows)
            : newRows;

        // Update the react state value
        _setRows(value);

        // Sync with react-hook-form
        field.onChange(value);
    }

    // State for DataGrid row editing mode
    const [rowModesModel, setRowModesModel] = React.useState<GridRowModesModel>({});
    const handleRowModesModelChange = (newRowModesModel: GridRowModesModel) => {
        setRowModesModel(newRowModesModel);
    };

    const handleRowEditStop: GridEventListener<'rowEditStop'> = (params, event) => {
        console.log("row turns to view mode:", params, event);
    };

    const processRowUpdate = (newRow: GridRowModel) => {
        const updatedRow = { ...newRow, isNew: false };
        setRows(rows.map((row) => (row.id === newRow.id ? updatedRow : row)));
        return updatedRow;
    };

    // Create an empty row for adding new record functionality
    const emptyRow = getEmptyRow(question);

    // Row editing edit handler
    const handleEditClick = (id: GridRowId) => () => {
        setRowModesModel({ ...rowModesModel, [id]: { mode: GridRowModes.Edit } });
    };

    // Row editing save handler
    const handleSaveClick = (id: GridRowId) => () => {
        setRowModesModel({ ...rowModesModel, [id]: { mode: GridRowModes.View } });
    };

    // Row editing delete handler
    const handleDeleteClick = (id: GridRowId) => () => {
        setRows(rows.filter((row) => row.id !== id));
    };

    // Row editing cancel handler
    const handleCancelClick = (id: GridRowId) => () => {
        setRowModesModel({
            ...rowModesModel,
            [id]: { mode: GridRowModes.View, ignoreModifications: true },
        });

        const editedRow = rows.find((row) => row.id === id);
        if (editedRow!.isNew) {
            setRows(rows.filter((row) => row.id !== id));
        }
    };

    // Define column definitions for the DataGrid
    const columns: GridColDef[] = getHeaders({
        question,
        rowModesModel,
        handleEditClick,
        handleDeleteClick,
        handleSaveClick,
        handleCancelClick,
    });

    return (
        <Box className="w-full">
            <Typography variant="h6">
                {question.labelText}
            </Typography>
            {question.o.description && <p>{question.o.description}</p>}

            <DataGrid
                rows={rows}
                columns={columns}
                editMode="row"
                rowModesModel={rowModesModel}
                // Disable the the column features, sorting, filtering, etc.
                disableColumnFilter={true}
                disableColumnSorting={true}
                disableColumnMenu={true}
                disableColumnResize={true}
                // Autosizing is glitching; using fluid with with header `flex` property
                disableAutosize={true}
                onRowModesModelChange={handleRowModesModelChange}
                // onRowEditStop={handleRowEditStop}
                processRowUpdate={processRowUpdate}
                // Replace the default footer with a custom one
                hideFooter={false}
                hideFooterSelectedRowCount={true}
                hideFooterPagination={true}
                slots={{ footer: CustomFooterComponent }}
                slotProps={{
                    footer: { setRows, setRowModesModel, emptyRow },
                }}
                // display: 'grid' is required for auto-shrinking when sidebar is closed
                // https://stackoverflow.com/questions/77902885/width-of-the-mui-x-data-grid-becoming-larger-than-the-parent-space-and-stretchin
                sx={{ display: 'grid' }}
            />
            {fieldState.invalid &&
                <FormHelperText error>
                    {fieldState.error?.message}
                </FormHelperText>
            }
        </Box>
    );
}


function getHeaders({
    question,
    rowModesModel,
    handleEditClick,
    handleDeleteClick,
    handleSaveClick,
    handleCancelClick,
}: {
    question: Question;
    rowModesModel: GridRowModesModel;
    handleEditClick: (id: GridRowId) => () => void;
    handleDeleteClick: (id: GridRowId) => () => void;
    handleSaveClick: (id: GridRowId) => () => void;
    handleCancelClick: (id: GridRowId) => () => void;
}): GridColDef[] {
    const columns: GridColDef[] = (question.o.grid_columns || []).map((column, _) => {
        // Corresponding column type
        let columnType: GridColDef['type'];
        switch (column.type) {
            case "number":
                columnType = "number";
                break;
            case "checkbox":
                columnType = "boolean";
                break;
            case "select":
                columnType = "singleSelect";
                break;
            case "date":
                columnType = "date";
                break;
            default:
                columnType = "string";
        }

        const columnFlex = columnType === "boolean" ? 0.5 : 1;

        return {
            field: column.label,
            headerName: column.label,
            description: column.description,
            // Material UI column attributes
            type: columnType,
            valueOptions: columnType === "singleSelect" && column.select_options
                ? column.select_options
                : null,
            editable: true,
            sortable: false,
            headerAlign: "center",
            flex: columnFlex,
        }
    });
    // console.log("Grid columns:", columns);

    // The actions column for editing and deleting rows
    columns.push({
        type: "actions",
        field: "actions",
        headerName: "Actions",
        flex: 0.5,
        getActions: ({ id }) => getEditActions({
            id,
            isInEditMode: rowModesModel[id]?.mode === GridRowModes.Edit,
            handleEditClick,
            handleDeleteClick,
            handleSaveClick,
            handleCancelClick,
        }),
    })

    return columns;
}

function getInitialRows(question: Question): GridRowsProp {
    const rows = (question.values ?? []).map((value, _) => {
        const row: GridRowModel = {};
        // Unique ID for each row
        row['id'] = uuidv6();

        // Populate the row with values
        question.o.grid_columns?.forEach((column, columnIndex) => {
            row[column.label] = value[columnIndex] ?? null;
        });
        return row;
    });

    // console.log("Grid rows:", rows);

    return rows as GridRowsProp;
}

function getEmptyRow(question: Question) {
    const row: { [key: string]: PrimitiveType } = {};
    // Populate the row with values
    question.o.grid_columns?.forEach((column, _) => {
        row[column.label] = '';
    });
    return row;
}

function getEditActions({
    id,
    isInEditMode,
    handleEditClick,
    handleDeleteClick,
    handleSaveClick,
    handleCancelClick,
}: {
    id: GridRowId;
    isInEditMode: boolean;
    handleEditClick: (id: GridRowId) => () => void;
    handleDeleteClick: (id: GridRowId) => () => void;
    handleSaveClick: (id: GridRowId) => () => void;
    handleCancelClick: (id: GridRowId) => () => void;
}) {

    if (isInEditMode) {
        return [
            <GridActionsCellItem
                key={`${id}-save`}
                icon={<SaveIcon />}
                label="Save"
                onClick={handleSaveClick(id)}
            />,
            <GridActionsCellItem
                key={`${id}-cancel`}
                icon={<CancelIcon />}
                label="Cancel"
                className="textPrimary"
                onClick={handleCancelClick(id)}
                color="inherit"
            />,
        ];
    }

    return [
        <GridActionsCellItem
            key={`${id}-edit`}
            icon={<EditIcon />}
            label="Edit"
            className="textPrimary"
            onClick={handleEditClick(id)}
            color="inherit"
        />,
        <GridActionsCellItem
            key={`${id}-delete`}
            icon={<DeleteIcon />}
            label="Delete"
            onClick={handleDeleteClick(id)}
            color="inherit"
        />,
    ];
}


function CustomFooterComponent(props: GridSlotProps['footer']) {
    const { setRows, setRowModesModel, emptyRow } = props;
    // First field to focus on
    const firstField = Object.keys(emptyRow)[0];

    const handleClick = () => {
        // The new row ID
        const newId = uuidv6();

        setRows((oldRows) => [
            ...oldRows,
            { id: newId, ...emptyRow, isNew: true },
        ]);

        setRowModesModel((oldModel) => ({
            ...oldModel,
            [newId]: { mode: GridRowModes.Edit, fieldToFocus: firstField },
        }));
    };

    return (
        <Toolbar>
            {/* Use explicit button instead of ToolbarButton */}
            {/* <Tooltip title="Add record">
                <ToolbarButton onClick={() => { }}>
                    <AddIcon fontSize="small" />
                </ToolbarButton>
            </Tooltip> */}
            <Button variant="outlined" startIcon={<AddIcon />} onClick={handleClick}>
                Add Record
            </Button>
        </Toolbar>
    );
}