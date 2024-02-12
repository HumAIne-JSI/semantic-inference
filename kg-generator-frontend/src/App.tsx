import React from "react";
import "./App.css";
import { TextField } from "@mui/material";
import Stack from "@mui/material/Stack";
import { Button } from "@mui/material";
import { Select, MenuItem, InputLabel, FormControl } from "@mui/material";
import TriplesTable, { Triple } from "./TriplesTable";
import { useMutation } from "@tanstack/react-query";
import axios from "axios";

enum OperationType {
  Query = "Query",
  AddJSONTriples = "Add triples (JSON)",
}

function App() {
  const [input, setInput] = React.useState("");
  const [queryInput, setQueryInput] = React.useState("");
  const [tableTriples, setTableTriples] = React.useState<Triple[]>([]);
  const [queryOutput, setQueryOutput] = React.useState<string>("");
  const [operationType, setOperationType] = React.useState<OperationType>(
    OperationType.Query,
  );
  const [gettingTriplesFromMultipleFiles, setGettingTriplesFromMultipleFiles] =
    React.useState(false);
  const serverAddress =
    process.env.REACT_APP_SERVER_ADDRESS || "http://127.0.0.1:5000";

  const getTriplesFromJson = useMutation({
    mutationFn: (json_string: string) => {
      return axios.post(serverAddress + "/get-triples-from-json", {
        json_string,
      });
    },
    onSuccess: (response) => {
      setTableTriples((prevTriples) => [
        ...prevTriples,
        ...response.data.triples,
      ]);
    },
  });

  const runQuery = useMutation({
    mutationFn: () => {
      return axios.post(serverAddress + "/query", {
        query: queryInput,
      });
    },
    onSuccess: (response) => {
      setQueryOutput(response.data.answer);
    },
  });

  const commitTriples = useMutation({
    mutationFn: (triples: Triple[]) => {
      return axios.post(serverAddress + "/commit-triples", {
        triples,
      });
    },
    onSuccess: (response) => {
      console.log("commited", response);
    },
  });

  const isLoadingTable =
    commitTriples.isPending ||
    getTriplesFromJson.isPending ||
    gettingTriplesFromMultipleFiles;

  const inputComponents = {
    [OperationType.Query]: (
      <TextField
        value={queryInput}
        id="input"
        label="Query Input"
        placeholder="Type query"
        multiline
        variant="outlined"
        sx={{
          root: {
            "& .MuiTextField-root": {
              margin: 1,
            },
          },
          textarea: {
            resize: "vertical",
            maxHeight: "calc(100vh - 200px)",
            minHeight: "20px",
          },
        }}
        maxRows={1}
        onChange={(e) => setQueryInput(e.target.value)}
      />
    ),

    [OperationType.AddJSONTriples]: (
      <TextField
        value={input}
        id="input"
        label="JSON Input"
        placeholder="Input JSON object (it's good, but not necessary, that object values in json have an id field with a unique value)"
        multiline
        variant="outlined"
        sx={{
          root: {
            "& .MuiTextField-root": {
              margin: 1,
            },
          },
          textarea: {
            resize: "vertical",
            maxHeight: "calc(100vh - 200px)",
            minHeight: "20px",
          },
        }}
        maxRows={1}
        onChange={(e) => setInput(e.target.value)}
      />
    ),
  };

  const outputComponents = {
    [OperationType.Query]: (
      <TextField
        value={queryOutput}
        disabled
        id="outlined-textarea"
        label={runQuery.isPending ? "Loading Answer..." : "Answer"}
        multiline
        variant="outlined"
        sx={{
          root: {
            "& .MuiTextField-root": {
              margin: 1,
            },
          },
          "& .MuiInputBase-root": {
            flexGrow: 1,
          },
          textarea: {
            minHeight: "50px",
          },
          flexGrow: 1,
          "& .MuiInputBase-input.Mui-disabled": {
            WebkitTextFillColor: runQuery.isPending ? "disabled" : "#000000",
          },
          "& textarea": {
            alignSelf: "flex-start",
          },
        }}
      />
    ),
    [OperationType.AddJSONTriples]: (
      <TriplesTable
        serverAddress={serverAddress}
        commitTriplesFunction={commitTriples.mutate}
        isLoading={isLoadingTable}
        triples={tableTriples}
        setTriples={setTableTriples}
      />
    ),
  };

  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
        alignContent: "stretch",
        justifyContent: "stretch",
      }}
    >
      <Stack direction="row" flexGrow={1} maxWidth="100%">
        <Stack
          direction="column"
          justifyContent="stretch"
          alignItems="stretch"
          flexGrow={1}
          padding={1}
          spacing={2}
          maxHeight="100%"
          minWidth={0}
        >
          {inputComponents[operationType]}
          {outputComponents[operationType]}
        </Stack>
        <Stack
          direction="column"
          padding={1}
          spacing={1}
          alignItems="stretch"
          minWidth={200}
        >
          <FormControl>
            <InputLabel id="select-operation-label">
              Select operation
            </InputLabel>
            <Select
              labelId="select-operation-label"
              id="demo-simple-select"
              value={operationType}
              label="Select operation"
              onChange={(e) => {
                setOperationType(e.target.value as OperationType);
              }}
            >
              {Object.entries(OperationType).map(([key, value]) => {
                return <MenuItem value={value}>{value}</MenuItem>;
              })}
            </Select>
          </FormControl>
          <input
            style={{ display: "none" }}
            id="contained-button-file"
            multiple={false}
            type="file"
            onChange={async (e) => {
              if (e.target.files && e.target.files[0]) {
                let res = await e.target.files[0].text();
                if (operationType == OperationType.Query) setQueryInput(res);
                else setInput(res);
              }
            }}
          />
          <label htmlFor="contained-button-file">
            <Button
              variant="contained"
              color="primary"
              fullWidth
              component="span"
            >
              Upload Text
            </Button>
          </label>
          {operationType === OperationType.AddJSONTriples ? (
            <React.Fragment>
              <Button
                variant="contained"
                color="primary"
                fullWidth
                component="span"
                onClick={() => {
                  getTriplesFromJson.mutate(input);
                }}
              >
                Add triples
              </Button>
              <input
                style={{ display: "none" }}
                id="contained-button-multiple-files"
                type="file"
                multiple={true}
                onChange={async (e) => {
                  if (e.target.files) {
                    setGettingTriplesFromMultipleFiles(true);
                    for (let file of Array.from(e.target.files)) {
                      let res = await file.text();
                      getTriplesFromJson.mutate(res);
                    }
                    setGettingTriplesFromMultipleFiles(false);
                  }
                }}
              />
              <label htmlFor="contained-button-multiple-files">
                <Button
                  variant="contained"
                  color="primary"
                  fullWidth
                  component="span"
                >
                  Add triples from files
                </Button>
              </label>
            </React.Fragment>
          ) : (
            <Button
              variant="contained"
              color="primary"
              fullWidth
              component="span"
              onClick={() => {
                runQuery.mutate();
              }}
            >
              Run Query
            </Button>
          )}
        </Stack>
      </Stack>
    </div>
  );
}

export default App;
