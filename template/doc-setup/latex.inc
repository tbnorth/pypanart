% Overwrite \begin{figure}[htbp] with \begin{figure}[H]
\usepackage{float}
\let\origfigure=\figure
\let\endorigfigure=\endfigure
\renewenvironment{figure}[1][]{
  \origfigure[H]
}{
  \endorigfigure
}

% \usepackage{helvet}
% \renewcommand{\familydefault}{\sfdefault}

% \usepackage[charter]{mathdesign}
% \def\rmdefault{bch} % not scaled

% \usepackage{inconsolata}

\usepackage[margin=1cm]{caption}

\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhead{}
\renewcommand{\headrulewidth}{0.0pt}
\fancyfoot[CO,CE]{\tiny {{C._metadata.run.time}}}
\fancyfoot[RE,RO]{\thepage}
\fancyfoot[LE,LO]{\tiny {{C._metadata.status}} {{C._metadata.run.commit_short}}}
\fancypagestyle{plain}{\thispagestyle{fancy}}
