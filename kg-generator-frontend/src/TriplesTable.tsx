import { useMemo } from "react";
import {
  MaterialReactTable,
  useMaterialReactTable,
  type MRT_ColumnDef,
  MRT_GlobalFilterTextField,
  MRT_ToggleFiltersButton,
  MRT_ToggleFullScreenButton,
  MRT_ToggleDensePaddingButton,
} from "material-react-table";
import { Box, Button, IconButton, Tooltip, Typography } from "@mui/material";
import React from "react";
import DeleteIcon from "@mui/icons-material/Delete";

export type BasicTriple = {
  subject: string;
  predicate: string;
  object: string;
};

export type Triple = {
  readable: BasicTriple;
  processed: BasicTriple;
};

interface TriplesTableProps {
  serverAddress: string;
  isLoading: boolean;
  commitTriplesFunction: (triples: Triple[]) => void;
  triples: Triple[];
  setTriples: React.Dispatch<React.SetStateAction<Triple[]>>;
}

const TriplesTable = (props: TriplesTableProps) => {
  const columns = useMemo<MRT_ColumnDef<Triple>[]>(
    () => [
      {
        accessorKey: "readable.subject", //access nested data with dot notation
        header: "Subject",
      },
      {
        accessorKey: "readable.predicate",
        header: "Predicate",
      },
      {
        accessorKey: "readable.object", //normal accessorKey
        header: "Object",
      },
    ],
    [],
  );

  const table = useMaterialReactTable({
    columns,
    data: props.triples, //data must be memoized or stable (useState, useMemo, defined outside of this component, etc.)
    enableStickyHeader: true,
    enableStickyFooter: true,
    initialState: {
      showColumnFilters: true,
      showGlobalFilter: true,
      columnPinning: {
        left: ["mrt-row-expand", "mrt-row-select"],
        right: ["mrt-row-actions"],
      },
    },
    state: {
      isLoading: props.isLoading,
    },
    muiTablePaperProps: {
      sx: {
        flexGrow: 100,
        minHeight: "0",
        display: "flex",
        flexDirection: "column",
      },
    },
    muiBottomToolbarProps: { sx: { marginTop: "auto" } },
    enableRowSelection: true,
    muiPaginationProps: { rowsPerPageOptions: [5, 10, 20, 50, 100] },
    enableSelectAll: true,
    selectAllMode: "all",
    renderTopToolbar: ({ table }) => {
      const selectedIndices = table
        .getSelectedRowModel()
        .flatRows.map((row) => row.index);

      const handleCommit = () => {
        props.commitTriplesFunction(
          table.getSelectedRowModel().flatRows.map((row) => row.original),
        );
        console.log("commit ", table.getSelectedRowModel().flatRows);
        // handleDelete();
      };

      const handleDelete = () => {
        console.log("delete ");
        table.resetRowSelection();
        props.setTriples((prevTriples) =>
          prevTriples.filter((_, index) => {
            return selectedIndices.indexOf(index) == -1;
          }),
        );
      };

      return (
        <Box
          sx={{
            backgroundColor: selectedIndices.length > 0 ? "lightblue" : "white",
            display: "flex",
            gap: "0.5rem",
            p: "8px",
            justifyContent: "space-between",
          }}
        >
          <Box sx={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            {/* import MRT sub-components */}
            <MRT_GlobalFilterTextField table={table} />
            <MRT_ToggleFiltersButton table={table} />
            <MRT_ToggleFullScreenButton table={table} />
            <MRT_ToggleDensePaddingButton table={table} />
            {selectedIndices.length > 0 ? (
              <Typography variant="body1">
                Selected {selectedIndices.length} out of {props.triples.length}{" "}
                triples
              </Typography>
            ) : null}
          </Box>
          <Box>
            <Box sx={{ display: "flex", gap: "0.5rem" }}>
              <Button
                variant="contained"
                color="primary"
                component="span"
                onClick={handleCommit}
                sx={{ whiteSpace: "nowrap", margin: 1 }}
                disabled={selectedIndices.length === 0}
              >
                Commit triples
              </Button>
              <Tooltip title="Delete">
                <IconButton
                  onClick={handleDelete}
                  disabled={selectedIndices.length === 0}
                >
                  <DeleteIcon />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>
        </Box>
      );
    },
  });

  return (
    <Box
      sx={{
        width: "100%",
        flexGrow: 100,
        minHeight: "0",
        maxWidth: "100%",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <MaterialReactTable table={table} />
    </Box>
  );
};

export default TriplesTable;
