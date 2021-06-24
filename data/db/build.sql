CREATE TABLE IF NOT EXISTS users (
    userID integer PRIMARY KEY NOT NULL,
    msgXP integer DEFAULT 0,
    renderXP integer DEFAULT 0,
    XPLock text DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS submission (
    userID integer,
    msgID integer PRIMARY KEY NOT NULL,
    votingMsgID integer,
    challengeID integer NOT NULL,
    FOREIGN KEY (challengeID) REFERENCES challenges (challengeID)

    FOREIGN KEY (userID) REFERENCES users (userID)
);

CREATE TABLE IF NOT EXISTS votes (
    votingMsgID integer,
    voterID integer,
    vote integer DEFAULT 0,
	PRIMARY KEY (votingMsgID, voterID),
	FOREIGN KEY (VotingMsgID) REFERENCES submissions (votingMsgID),
    FOREIGN KEY (voterID) REFERENCES users (userID)
);

CREATE TABLE IF NOT EXISTS challengeTypes (
    challengeTypeID integer PRIMARY KEY,
    challengeTypeDescription text
);

CREATE TABLE IF NOT EXISTS themes (
    themeName text PRIMARY KEY,
    themeStatus integer DEFAULT 0,
    lastUsed text DEFAULT '2011-11-11 11:11:11' NOT NULL
);

CREATE TABLE IF NOT EXISTS challenge (
    challengeTypeID integer DEFAULT 0,
    themeName text NOT NULL,
    challengeID integer PRIMARY KEY AUTOINCREMENT NOT NULL,
    startDate text DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (themeName) REFERENCES themes (themeName)
    FOREIGN KEY (challengeTypeID) REFERENCES challengeTypes (challengeTypeID)
);

INSERT OR IGNORE INTO challengeTypes (challengeTypeID, challengeTypeDescription) VALUES (0, "Daily challenge"), (1, "Weekly challenge");


