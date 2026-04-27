---
icon: lucide/book-open
---

<style>
  /* This page starts at 5 */
  .md-typeset {
    counter-reset: h1-count 4 !important; 
  }

  /* This specific page sidebar starts at 5 */
  .md-nav--primary {
    counter-reset: toc1 5 !important;
  }
</style>

# Shell Commands

You will be using shell commands if you are operating on Linux or macOS to write your documentation. This page serves as a refresher on the essential commands for navigating and managing your system using either bash or zsh, the latter being the default shell in the macOS terminal.

!!! tip

    A detailed reference to the shell commnand line can be found on [linuxcommand.org](https://linuxcommand.org){target="_blank"}.

## Navigation and basic info

Knowing where you are and how to move is the first step to understanding bash/zsh.

| Command | Action |
| -- |-- |
| `pwd` | Print Working Directory: Shows exactly where you are. |
| `ls` | List: Shows files in the current folder. |
| `ls -la` | List All: Shows hidden files and detailed info (sizes, dates). |
| `cd [dir]` | Change Directory: Move to a folder (e.g., cd Documents). |
| `cd ..` | Go Up: Moves one level up to the parent folder. |
| `cd ~` | Home: Takes you back to your user folder. |
| `clear` | Cleans up the terminal screen (Shortcut: Cmd + K). |

## File and Folder Operations

Next the shell commands to manage directories and files.

!!! Warning
    A shell does not have a "Trash" bin. When you delete something here, it is usually gone for good.

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

## Administrative and Permissions

!!! Note
    If you get a "Permission Denied" error, you likely need sudo.


| Command | Action |
| -- |-- |
| `sudo [cmd]` | SuperUser Do: Runs a command with admin privileges. |
| `chmod 755 [file]` | Changes permissions (755 is standard for executable scripts). |
| `chown [user] [file]` | Changes the owner of a file. |
| `history` | Shows a list of all recently used commands. |

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
| `tail -f [file]` | This is the "Live" mode. It keeps the file open and updates the screen in real-time as new lines are added. This is how developers watch server logs as they happen. |


## Searching and Filtering

Essential commands for finding files and file contents.

| Command | Action |
| -- |-- |
| `grep "word" [file]` | Searches for a specific string inside a file. |
| `find . -name "*.txt"` | Finds all .txt files in the current directory and subdirectories. |
| `[cmd] | grep "word"` | The Pipe (\|) takes the output of one command and sends it to another. |


## Stream Shortcuts

These operators allow you to pass data between running programs and files.

| Shortcut | Action |
| -- |-- |
| `>` | Overwrite: Sends output to a file, deleting whatever was there before. e.g. `echo "hello" > file.txt`
| `>>` | Append: Adds output to the end of a file without deleting the old stuff. e.g. `echo "world" >> file.txt`
| `|` | The Pipe: takes the "Standard Out" of the left command and shoves it into the "Standard In" of the right command. |

## Essential Keyboard Shortcuts

| Shortcut | Action |
| -- |-- |
| `Tab` | Auto-complete. Start typing a folder name and hit Tab. If it’s unique, it will finish it for you. |
| `Arrow Up/Down` | Scroll through your previous commands. |
| `Ctrl + C` | Cancel/Kill the currently running command. |


## Job Queue Control

| Shortcut/Command | Action |
| -- |-- |
| `[cmd] &` | Start in Background: Runs the command immediately in the background so you can keep typing. |
| `Ctrl + Z` | Suspend: Freezes the current foreground task and sends it to the background as a "stopped" job.
| `Ctrl + C` | Interrupt: Cancel/Kill the currently running command. |
| `Ctrl + \` | Quit: Force-quits a task and creates a "core dump" (rarely needed for casual use).
| `jobs` |	Lists all background/suspended jobs. |
| `fg %[id]` | Foreground: Brings a job back to the front so you can interact with it. |
| `bg %[id]` | Background: Tells a suspended job to start running again, but in the background. |
| `kill %[id]` |	Terminates a job in your list using its job number. |

## Jobs and Processes

| Command | Action |
| -- |-- |
| `ps` |	"Process Status." Use ps aux to see every running process. |
| `top` | A live, updating list of processes (sorted by CPU/Memory). Press q to exit. |
| `htop` | A prettier, interactive version of top (install via brew install htop). |
| `pgrep [name]` | Finds the PID of a process by name (e.g., pgrep Chrome). |
| `kill [PID]` | Sends a "polite" request to a process to stop (SIGTERM). |
| `kill -9 [PID]` | The "Executioner." Force-kills a process instantly (SIGKILL). |
| `killall [name]` | Kills all processes with a certain name (e.g., killall Finder). |