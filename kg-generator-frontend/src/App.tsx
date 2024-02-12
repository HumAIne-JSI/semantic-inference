import React, { useRef } from "react";
import logo from "./logo.svg";
import "./App.css";
import { TextField } from "@mui/material";
import { TextareaAutosize } from "@mui/base";
import Stack from "@mui/material/Stack";
import { Button } from "@mui/material";
import { Select, MenuItem, InputLabel, FormControl } from "@mui/material";
import TriplesTable, { Triple } from "./TriplesTable";
import { useMutation } from "@tanstack/react-query";
import axios from "axios";
import { table } from "console";

enum OperationType {
  Query = "Query",
  AddJSONTriples = "Add triples (JSON)",
}

function App() {
  const [input, setInput] = React.useState("");
  const [queryOutput, setQueryOutput] = React.useState<string>("");
  const [operationType, setOperationType] = React.useState<OperationType>(
    OperationType.Query,
  );
  const serverAddress =
    process.env.REACT_APP_SERVER_ADDRESS || "http://127.0.0.1:5000";

  const tableRef = useRef();
  const getTriplesFromJson = useMutation({
    mutationFn: (json_string: string) => {
      return axios.post(serverAddress + "/get-triples-from-json", {
        json_string,
      });
    },
    onSuccess: (response) => {
      if (tableRef.current) {
        //@ts-ignore
        tableRef.current.addTriples(response.data.triples);
      }
    },
  });

  const runQuery = useMutation({
    mutationFn: () => {
      return axios.post(serverAddress + "/query", {
        query: input,
      });
    },
    onSuccess: (response) => {
      setQueryOutput(response.data.answer);
    },
  });

  const inputComponents = {
    [OperationType.Query]: (
      <TextField
        value={input}
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
        onChange={(e) => setInput(e.target.value)}
      />
    ),

    [OperationType.AddJSONTriples]: (
      <TextField
        value={input}
        id="input"
        label="JSON Input"
        placeholder="Input JSON object (if the object has an 'id' key it is best if it is uniquely identified by it, e. g. there isn't something completely unrelated with the same 'id' value)"
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
        label="Answer"
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
            WebkitTextFillColor: "#000000",
          },
          "& textarea": {
            alignSelf: "flex-start",
          },
        }}
      />
    ),
    [OperationType.AddJSONTriples]: (
      <TriplesTable ref={tableRef} serverAddress={serverAddress} />
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
                setInput(res);
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
                  if (e.target.files && e.target.files[0]) {
                    for (let file of Array.from(e.target.files)) {
                      let res = await file.text();
                      getTriplesFromJson.mutate(res);
                    }
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
