CREATE TABLE IF NOT EXISTS users (
    userID integer PRIMARY KEY,
    msgXP integer DEFAULT 0,
    renderXP integer DEFAULT 0,
    XPLock text DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS submissions (
    userID integer,
    msgID integer PRIMARY KEY,
    challengeID integer,
    FOREIGN KEY (challengeID) REFERENCES challenges (challengeID)

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

CREATE TABLE IF NOT EXISTS themes (
    themeName text PRIMARY KEY,
    themeStatus integer DEFAULT 0,
    lastUsed text DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS challenge (
    challengeTypeID integer DEFAULT 0,
    themeName text NOT NULL,
    challengeID integer PRIMARY KEY AUTOINCREMENT,
    startDate text DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (themeName) REFERENCES themes (themeName)
    FOREIGN KEY (challengeTypeID) REFERENCES challengeTypes (challengeTypeID)
);

INSERT OR IGNORE INTO challengeTypes (challengeTypeID, challengeTypeDescription) VALUES (0, "Daily challenge"), (1, "Weekly challenge");


