CREATE TABLE IF NOT EXISTS alerts (
    gitCommit STRING PRIMARY KEY,
    bbpUrl STRING,
    company STRING,
    title STRING,
    jsFile STRING,
    regex STRING,
    createdAt DATE,
    severity STRING,
    state STRING,
    calledAt DATE,
    calledBy STRING
    );

CREATE TABLE IF NOT EXISTS fileMonitors(
    title STRING PRIMARY KEY,
    bbpUrl STRING,
    company STRING,
    frequency INTEGER,
    procModule STRING,
    lastRun DATE,
    createdAt DATE
);
