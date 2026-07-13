---
icon: lucide/book-open
---

<!-- 
# Copyright (c) 2025-2026 Mark Buckwell and contributors
# SPDX-License-Identifier: MIT
-->

{{ heading_counter_reset(page) }}

# Shell commands

You will be using shell commands if you are operating on Linux or macOS to write your documentation. This section serves as a refresher on the essential commands for navigating and managing your system using either bash or zsh.

!!! tip

    You can find a more detailed reference to the shell command line on [linuxcommand.org](https://linuxcommand.org){target="_blank"}.

## Navigation and basic info

Knowing where you are and how to move is the first step to understanding bash/zsh.

| Command | Action |
| -- |-- |
| `pwd` | Print Working Directory: Shows exactly where you are. |
| `ls` | List: Shows files in the current folder. |
| `ls -la` | List All: Shows hidden files and detailed info (sizes, dates). |
| `cd [dir]` | Change Directory: Move to a folder (For example, cd Documents). |
| `cd ..` | Go Up: Moves one level up to the parent folder. |
| `cd ~` | Home: Takes you back to your user folder. |
| `clear` | Cleans up the terminal screen (Shortcut: Cmd + K). |
/// table-caption | <
Basic navigation commands
///

## File and folder operations

Next, here are the shell commands to manage directories and files. You will be using these commands to create, copy, move, and delete files and folders.

!!! Warning
    A shell doesn't have a "Trash" bin. When you delete something here, it's usually gone for good.

| Command | Action |
| -- |-- |
| `mkdir [name]` | Make Directory: Creates a new folder. |
| `touch [file]` | Creates a new empty file. |
| `cp [src] [dest]`	| Copy: Duplicates a file. Use cp -r for folders. |
| `mv [src] [dest]`	| Move: Also used to rename files. |
| `rm [file]` | Remove: Deletes a file. |
| `rm -rf [dir]` | Force Remove: Deletes a folder and everything inside (Use with care!). |
| `cat [file]` | Displays the entire contents of a file in the terminal. |
| `less [file]` | Opens a file for reading (press q to exit). |
/// table-caption | <
File and folder operations
///

## Editing files

You will need to edit files in the terminal. There are many editors available, each with its own strengths and weaknesses. Here are some popular options:

| Editor | Style | Best For |
| -- |-- |-- |
| `nano` | Lightweight / Modeless | Quick, beginner-friendly configuration edits. |
| `vim`/`neovim` | Modal / Highly Keyboard-Driven | Rapid editing, coding, and heavy terminal workflows. |
| `micro` | Modern / Modeless | A modern terminal editor with intuitive Ctrl+C/Ctrl+V shortcuts and mouse support. |
| `helix` | Modal / Modern | A modern, fast terminal editor with built-in language server support and multiple cursors. |
| `emacs` | Extendable Environment | Users who want an entire operating system of utilities inside their editor. |
/// table-caption | <
Terminal text editors
///

If you are new to terminal editors, start with `nano` or `micro`. If you want to learn a more powerful editor, try `vim` or `helix`.

## Administrative and permissions

Often the permissions of files and folders will need changing. Here are some commands to help you manage permissions and ownership.

!!! Note
    If you get a "Permission Denied" error, you likely need sudo.

| Command | Action |
| -- |-- |
| `sudo [cmd]` | SuperUser Do: Runs a command with admin privileges. |
| `chmod 755 [file]` | Changes permissions (755 is standard for executable scripts). |
| `chown [user] [file]` | Changes the owner of a file. |
| `history` | Shows a list of all recently used commands. |
/// table-caption | <
Administrative and permissions commands
///

## Viewing content

Handling text files with shell commands.

| Command | Action |
| -- |-- |
| `cat` |	Concatenate: Dumps the whole file to your screen.	Best for short files. |
| `tac` |	Reverse cat: Displays the file starting from the last line.	Great for seeing the newest entries in a log first. |
| `nl` | Number Lines: Displays file content with line numbers.	Use `nl -ba` to number every single line, including blanks. |
| `more` | The "classic" version. It lets you scroll down using the Spacebar. Once you reach the end, it exits automatically. |
| `less` | A more powerful version of 'more'. It doesn't load the whole file at once (it's faster). You can scroll up (using the arrow keys) and you can search within the text (press / then type your word).
| `head -n 20 [file]` | Shows you the top 20 lines of a file. |
| `tail -n 20 [file]` | Shows you the bottom 20 lines. |
| `tail -f [file]` | This is the "Live" mode where the option keeps the file open and updates the screen in real-time from file additions. This is how developers watch server logs as they happen. |
/// table-caption | <
Viewing file content
///

## Searching and filtering

Essential commands for finding files and file contents.

| Command | Action |
| -- |-- |
| `grep "word" [file]` | Searches for a specific string inside a file. |
| `find . -name "*.txt"` | Finds all .txt files in the current directory and subdirectories. |
| `[cmd] | grep "word"` | The Pipe (\|) takes the output of one command and sends it to another. |
/// table-caption | <
Searching and filtering commands
///

## Essential keyboard shortcuts

There are some essential keyboard shortcuts to help you navigate the terminal more efficiently.

| Shortcut | Action |
| -- |-- |
| `Tab` | Auto complete. Start typing a folder name and hit Tab. If it's unique, it will finish it for you. |
| `Arrow Up/Down` | Scroll through your previous commands. |
| `Ctrl + C` | Cancel/Kill the currently running command. |
/// table-caption | <
Essential keyboard shortcuts
///

## Stream shortcuts

Programs and files pass data between themselves using the operators below.

| Shortcut | Action |
| -- |-- |
| `>` | Overwrite: Sends output to a file, deleting whatever was there before. For example, `echo "hello" > file.txt`
| `>>` | Append: Adds output to the end of a file without deleting the old stuff. For example, `echo "world" >> file.txt`
| `|` | The Pipe: takes the "Standard Out" of the left command and shoves it into the "Standard In" of the right command. |
/// table-caption | <
Stream redirection operators
///

## Job queue control

There are commands to manage jobs running in the background or suspended in the terminal. It's important to understand that a job is a command that's running in the terminal. You can have multiple jobs running at the same time, and you can control them using these commands.

| Shortcut/Command | Action |
| -- |-- |
| `[cmd] &` | Start in Background: Runs the command immediately in the background so you can keep typing. |
| `Ctrl + Z` | Suspend: Freezes the current foreground task and sends it to the background as a "stopped" job.
| `Ctrl + C` | Interrupt: Cancel/Kill the currently running command. |
| `Ctrl + \` | Quit: Force-quits a task and creates a "core dump" (Not often needed for casual use).
| `jobs` |	Lists all background/suspended jobs. |
| `fg %[id]` | Foreground: Brings a job back to the front so you can interact with it. |
| `bg %[id]` | Background: Tells a suspended job to start running again, but in the background. |
| `kill %[id]` |	Terminates a job in your list using its job number. |
/// table-caption | <
Job control shortcuts
///

## Jobs and processes

There are commands available to manage processes and jobs running on your system. A process is a program that's currently running, and each process has a unique Process ID (PID).

| Command | Action |
| -- |-- |
| `ps` |	"Process Status." Use ps aux to see every running process. |
| `top` | A live, updating list of processes (sorted by CPU/Memory). Press q to exit. |
| `htop` | A prettier, interactive version of top (install via brew install htop). |
| `pgrep [name]` | Finds the PID of a process by name (For example, pgrep Chrome). |
| `kill [PID]` | Sends a "polite" request to a process to stop (SIGTERM). |
| `kill -9 [PID]` | The "Executioner." Force-kills a process instantly (SIGKILL). |
| `killall [name]` | Kills all processes with a certain name (For example, killall Finder). |
/// table-caption | <
Process management commands
///

## Where to go next

Continue to [Testing](testing.md) if you're contributing to the template itself, or jump straight to [Finalising your document](customise.md#finalising-your-document) in Customisation once your report is ready to submit.
