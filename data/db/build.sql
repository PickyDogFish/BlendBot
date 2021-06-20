CREATE TABLE IF NOT EXISTS users (
    userID integer PRIMARY KEY,
    msgXP integer DEFAULT 0,
    renderXP integer DEFAULT 0,
    XPLock text DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS submissions (
    userID integer,
    msgID integer PRIMARY KEY,
    voteDay text DEFAULT (datetime('now', 'localtime')),
    challengeType integer,
    FOREIGN KEY (challengeType) REFERENCES challengeTypes (challengeTypeID),

    FOREIGN KEY (userID) REFERENCES users (userID)
);

CREATE TABLE IF NOT EXISTS votes (
    msgID integer,
    voterID integer,
    vote integer DEFAULT 0,
	PRIMARY KEY (msgID, voterID),
	FOREIGN KEY (msgID) REFERENCES submissions (msgID),
    FOREIGN KEY (voterID) REFERENCES users (userID)
);

CREATE TABLE IF NOT EXISTS challengeTypes (
    challengeTypeID integer PRIMARY KEY,
    challengeTypeDescription text
);

