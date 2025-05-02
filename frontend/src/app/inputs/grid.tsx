import { GridQuestion } from "@/app/data/FormData";
import AddIcon from '@mui/icons-material/Add';
import CancelIcon from '@mui/icons-material/Close';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import SaveIcon from '@mui/icons-material/Save';
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import {
    DataGrid,
    GridActionsCellItem,
    GridColDef,
    GridEventListener,
    GridRowEditStopReasons,
    GridRowId,
    GridRowModel,
    GridRowModes,
    GridRowModesModel,
    GridRowsProp,
    GridSlotProps,
    Toolbar
} from '@mui/x-data-grid';
import React from 'react';
import { v6 as uuidv6 } from 'uuid';

// Declare custom props to pass to the footer component
// See https://mui.com/x/api/data-grid/data-grid/#data-grid-prop-slotProps
declare module '@mui/x-data-grid' {
    interface FooterPropsOverrides {
        setRows: (newRows: (oldRows: GridRowsProp) => GridRowsProp) => void;
        setRowModesModel: (
            newModel: (oldModel: GridRowModesModel) => GridRowModesModel,
        ) => void;
        emptyRow: { [key: string]: any };
    }
}

export default function GridInput({
    question,
}: Readonly<{
    question: GridQuestion;
}>) {
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
        <div className="w-full mt-8">
            <Typography variant="h5">{question.label}</Typography>
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
    question: GridQuestion;
    rowModesModel: GridRowModesModel;
    handleEditClick: (id: GridRowId) => () => void;
    handleDeleteClick: (id: GridRowId) => () => void;
    handleSaveClick: (id: GridRowId) => () => void;
    handleCancelClick: (id: GridRowId) => () => void;
}): GridColDef[] {
    const columns: GridColDef[] = question.columns.map((column, _) => {
        // Corresponding column type
        let columnType: GridColDef['type'];
        switch (column.type) {
            case "number":
                columnType = "number";
                break;
            case "checkbox":
                columnType = "boolean";
                break;
            // case "date":
            //     columnType = "date";
            //     break;
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

function getInitialRows(question: GridQuestion) {
    const rows = question.values.map((value, _) => {
        const row: { [key: string]: any } = {};
        // Unique ID for each row
        row['id'] = uuidv6();

        // Populate the row with values
        question.columns.forEach((column, columnIndex) => {
            row[column.label] = value[columnIndex] ?? null;
        });
        return row;
    });

    // console.log("Grid rows:", rows);

    return rows as GridRowsProp;
}

function getEmptyRow(question: GridQuestion) {
    const row: { [key: string]: any } = {};
    // Populate the row with values
    question.columns.forEach((column, _) => {
        row[column.label] = null;
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
                icon={<SaveIcon />}
                label="Save"
                onClick={handleSaveClick(id)}
            />,
            <GridActionsCellItem
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
            icon={<EditIcon />}
            label="Edit"
            className="textPrimary"
            onClick={handleEditClick(id)}
            color="inherit"
        />,
        <GridActionsCellItem
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