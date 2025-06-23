import AddIcon from '@mui/icons-material/Add';
import CancelIcon from '@mui/icons-material/Close';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import SaveIcon from '@mui/icons-material/Save';
import Button from "@mui/material/Button";
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
    GridRowEditStopReasons,
    GridRowModes,
    Toolbar,
} from '@mui/x-data-grid';
import React from 'react';
import { v6 as uuidv6 } from 'uuid';
import type { Question, PrimitiveType } from '../../context/FormTypes';

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

export function GridInput(question : Readonly<Question>) {
    // Populate rows with values from the question
    const initialRows = getInitialRows(question);

    // Create an empty row for adding new record functionality
    const emptyRow = getEmptyRow(question);

    const [rows, setRows] = React.useState(initialRows);
    const [rowModesModel, setRowModesModel] = React.useState<GridRowModesModel>({});

    const handleRowEditStop: GridEventListener<'rowEditStop'> = (params, event) => {
        if (params.reason === GridRowEditStopReasons.rowFocusOut) {
            event.defaultMuiPrevented = true;
        }
    };

    const handleEditClick = (id: GridRowId) => () => {
        setRowModesModel({ ...rowModesModel, [id]: { mode: GridRowModes.Edit } });
    };

    const handleSaveClick = (id: GridRowId) => () => {
        setRowModesModel({ ...rowModesModel, [id]: { mode: GridRowModes.View } });
    };

    const handleDeleteClick = (id: GridRowId) => () => {
        setRows(rows.filter((row) => row.id !== id));
    };

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

    const processRowUpdate = (newRow: GridRowModel) => {
        const updatedRow = { ...newRow, isNew: false };
        setRows(rows.map((row) => (row.id === newRow.id ? updatedRow : row)));
        return updatedRow;
    };

    const handleRowModesModelChange = (newRowModesModel: GridRowModesModel) => {
        setRowModesModel(newRowModesModel);
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
        <div className="w-full">
            <Typography variant="h6">{question.indexText}{question.label}</Typography>
            <p>{question.description}</p>

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
                onRowEditStop={handleRowEditStop}
                processRowUpdate={processRowUpdate}
                // Replace the default footer with a custom one
                hideFooter={false}
                hideFooterSelectedRowCount={true}
                hideFooterPagination={true}
                slots={{ footer: CustomFooterComponent }}
                slotProps={{
                    footer: { setRows, setRowModesModel, emptyRow },
                }}
            />
        </div>
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
    const columns: GridColDef[] = (question.grid_columns || []).map((column, _) => {
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

function getInitialRows(question: Question) {
    const rows = (question.values ?? []).map((value, _) => {
        const row: { [key: string]: PrimitiveType } = {};
        // Unique ID for each row
        row['id'] = uuidv6();

        // Populate the row with values
        question.grid_columns?.forEach((column, columnIndex) => {
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
    question.grid_columns?.forEach((column, _) => {
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


function CustomFooterComponent(
    props: GridSlotProps['footer']
) {
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