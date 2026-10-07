# Possible Prototype Directions and Partner Communication Evidence

**Project:** P631 Accelerating Opposition Analysis in Professional Rugby
**Team:** T243
**Author:** Ngoc Ha Nguyen (n12248746)
**Weeks covered:** 7 to 11

> Items in [square brackets] are placeholders for links or dates that need to be filled in from the Team's records before submission.

## Part A. Possible Prototype Directions

### A1. Starting point

Our Tutor advised that by the end of Phase 1 we should be able to demonstrate at least one working part of the overall solution. Each direction below is linked to a pain point raised by the Partner at the first meeting, so that the prototype is driven by the Partner's problem rather than by a technology choice.

| Pain point from the Partner meeting | Who raised it |
|---|---|
| Previously processed games are processed again every time | Dimitri (data analysis workflow) |
| The same raw files are read many times by separate notebooks | Dimitri |
| Several notebooks are run separately with manual switching between teams | Dimitri |
| The LaTeX and PDF preview is assembled manually at the end | Dimitri |
| Building Tableau outputs takes a long time | Jack (performance analysis workflow) |
| Many slides must be reviewed manually to find key findings | Jack |
| Statistics and footage are combined by hand | Jack |

### A2. Prototype ideas

**P1. Incremental extraction.** Keep a record of which fixtures have already been processed and store their results. When a new match file arrives, only that match is processed and then added to the stored results. This directly removes the repeated processing of old games.

**P2. Combined extraction.** Read each raw event file once and produce every analysis table (kicking, breakdown, tackling, linebreaks, intervals) in a single pass, instead of each notebook reading the same file again.

**P3. One-click workflow orchestration.** A single action that runs the full chain for a chosen opponent. Load the files, validate them, run every analysis module, and save the outputs. This replaces running notebooks one by one and switching between teams manually.

**P4. Automated report generation.** Generate the opposition preview document (PDF or slides) from the analysis outputs using a fixed template, including the Key Points page. This targets the manual LaTeX assembly and the time spent reviewing slides.

**P5. Automated data validation layer.** Run quality and consistency checks every time a file is loaded, for example checking that rebuilt points equal the final score, that times and coordinates are valid, and that required fields are present. This makes the outputs trustworthy without manual checking. A working version of these checks already exists (`validate_reds_dataset.py`).

**P6. Interactive opposition dashboard.** Filterable views of each analysis section with pitch maps, consistent colours and visible sample sizes. The Team's current Streamlit prototype already covers much of this direction.

### A3. Comparison of prototype options

Ratings: High, Medium or Low. "Fit with current data" reflects that the Partner has provided one representative fixture.

| Option | Pain point addressed | Main user | Fit with current data | Build effort | Demo value by end of Phase 1 | Depends on Partner for | Status in current prototype |
|---|---|---|---|---|---|---|---|
| P1 Incremental extraction | Repeated processing of old games | Data analyst | Low (needs several fixtures) | Medium | Medium | More fixture files | Not started. Pipeline already accepts multiple files |
| P2 Combined extraction | Same raw files read many times | Data analyst | High | Low to Medium | Medium | Nothing further | Largely in place. One load feeds all modules |
| P3 One-click orchestration | Manual running of separate notebooks | Data analyst | High | Medium | High | Existing notebooks, to compare steps | Partially in place through the upload workflow |
| P4 Automated report generation | Manual LaTeX assembly and slide review | Data and performance analysts | Medium (structure yes, season figures no) | Medium to High | High | Preferred output format and template | Not started |
| P5 Validation layer | Low trust in outputs, manual checking | Data analyst | High | Low | Medium | Field definitions | Working script, not yet built into the prototype |
| P6 Interactive dashboard | Time to build Tableau views and find insights | Performance analyst, coaches | High | Medium | High | Feedback on which views are useful | Supported for five sections |

### A4. Suggested direction (for Team discussion)

1. **For the end of Phase 1 demonstration:** combine P2, P3 and P5 into one clear story. Upload a Partner file, validate it automatically, and generate every analysis section in one step. This uses what the Team has already built, works fully with the data we have, and shows a measurable improvement over running several notebooks.
2. **First steps for Phase 2:** P1 and P4. Both depend on information we do not have yet, namely more fixture files and the Partner's preferred output format. At the first meeting the Partner mentioned around 5 to 6 sample games, but one representative fixture has been provided so far. Once those arrive, incremental extraction makes multi-match analysis practical, and automated report generation addresses the largest remaining manual step.
3. **Decision points still open:** whether the final output should replace, complement or export into the Partner's existing reporting tools, and whether Streamlit should stay as the main interface.

## Part B. Partner Communication Evidence

### B1. Communication log

| Date | Type | Summary | Evidence |
|---|---|---|---|
| Weeks 6 to 7 | Email (Team to Partner) | Introduced Team T243, confirmed interest in P631 and proposed meeting times | [link to email] |
| Weeks 6 to 7 | Email | First meeting confirmed for Friday 4 September | [link to email] |
| Before 4 September | Prepared questions | Questions on workflow, data, tools, pain points and expectations (Section B3) | [link to question document] |
| Friday 4 September 2026 | First Partner meeting | Discussion with Dimitri and Jack about current workflows and pain points (Section B2) | [Partner Meeting 1 Summary](IFB398_T243_Partner_Meeting_1_Summary.docx) |
| Weeks 8 to 9 | Email (Team to Partner) | Follow-up requesting the sample CSV files and existing notebooks discussed at the meeting | [link to email] |
| Weeks 9 to 11 [exact date] | Partner response | Representative event dataset (Reds v Waratahs), Q&A document and the Fijian Drua opposition preview were shared | [link] |
| Week 11 | Email draft (Team to Partner) | Clarification questions from data validation (Section B4) | [link once sent] |

### B2. First Partner meeting summary (Friday 4 September 2026)

The full summary is in [IFB398_T243_Partner_Meeting_1_Summary.docx](IFB398_T243_Partner_Meeting_1_Summary.docx). The key points are below.

**Attendees.** Dimitri (Data and Machine Learning Analyst) and Jack (Performance and Footage Analyst) from Queensland Rugby Union, and Team T243 members Dinh Tuan (Leon) Duong, Ngoc Ha (Emy) Nguyen, Nao Hakoda, Glunlada (Star) Kamonthitiwuth and Huynh Anh Quan (Kelvin) Dang. Supervisor Sarah Mitchell.

**Purpose.** To understand the current opposition-analysis process before deciding on any technical solution.

**Current workflow, data analysis (Dimitri).** Game CSV files are extracted and then processed through several separate analysis notebooks. These produce CSV outputs and figures, which are combined into a LaTeX preview and then a final PDF opposition report.

**Current workflow, performance analysis (Jack).** Opta statistics are turned into visualisations in Tableau, reviewed as PowerPoint slides to select key statistics, and then combined with footage prepared in SportsCode to create the opposition preview for coaches.

**Main pain points raised.**

1. Previously processed games are processed again.
2. The same raw files are read many times.
3. Multiple notebooks have to be run separately, with manual switching between teams.
4. Building Tableau outputs is time-consuming.
5. Many slides must be reviewed manually to find the key findings.
6. Statistics and footage are combined manually.

**Partner guidance.** Python is recommended when extending Dimitri's existing extraction code, and the solution is expected to run locally on the Partner's machines. All five Capstone teams work with the same context and data, and each team develops its own approach.

**Agreed actions.** The Partner would provide around 5 to 6 sample CSV game files and Dimitri's current notebooks. The Team would explore the data, understand the extraction process, set up a GitHub repository with the Partners as collaborators, and identify where the process can be improved or automated.

**Outcome for the project.** The meeting confirmed that the project is about reducing repetitive manual work in an existing process, not about creating new rugby analysis methods.

### B3. Questions we prepared for the Partner

The questions were grouped by theme so that the meeting could move from the current process to expectations.

**Current workflow**
1. Can you walk us through how an opposition preview is produced, from receiving the data to giving the report to coaches?
2. Which steps take the most time, and which are repeated for every opponent?
3. Who uses the final outputs, and what do they need from them?

**Data and tools**
4. What data sources are used, and in what format do they arrive?
5. Which tools, scripts or notebooks are currently used for each step?
6. Could we access sample data and the existing code or notebooks?

**Pain points and priorities**
7. Which part of the process would you most like to be faster or automated?
8. Are there any steps where errors or inconsistencies tend to happen?

**Expectations and constraints**
9. What would a successful outcome look like at the end of this semester?
10. Are there technical requirements, such as preferred languages, platforms or security rules for the data?
11. Is there earlier work, for example from previous capstone teams, that we should build on?
12. How would you prefer to communicate with the Team, and how often?

[Replace or adjust this list with the final version the Team used, and link the original document.]

### B4. Follow-up email to the Partner (Week 11 draft)

The first follow-up email, sent between Weeks 8 and 9, requested the sample files and notebooks. The Partner has since shared a representative dataset, so the draft below follows up on the questions raised during our data validation.

> **Subject:** P631 Team T243, clarification questions on the Reds v Waratahs dataset
>
> Dear Dimitri and Jack,
>
> Thank you for sharing the Reds v Waratahs event dataset, the Q&A document and the Fijian Drua opposition preview. They have helped us move our prototype from public data to your actual data structure.
>
> While checking the dataset, we confirmed that the event data accurately reproduces the final score of 26 to 17, which gives us good confidence in it. We also found a few points where your confirmation would make sure our calculations match your existing analysis.
>
> 1. What do action codes 28 and 29 represent? They appear 144 times each without an action name.
> 2. What are the x-coordinate boundaries of field zones A, B, M, C and D?
> 3. For Breakdown Choices, is the halfback's pass to the first receiver counted as a decision, or is only the final decision after each breakdown counted?
> 4. Does PlayNum correspond to the phase numbers in the preview, and what does PlayNum 0 mean?
> 5. Are "dominant tackles" in the preview based on the Dominant Tackle qualifier or on sacks?
> 6. Do end coordinates recorded as (0,0) mean that the end point was not recorded?
> 7. Would you be able to share additional fixtures, so that we can test multi-match and season-level analysis?
> 8. Would it be possible to see the existing notebooks, so that we can compare our pipeline with your current steps?
>
> We would also value your view on the preferred final output, for example an interactive dashboard, a generated PDF preview, or an export into your existing tools.
>
> If it is easier, we would be happy to discuss these points in a short online meeting at a time that suits you.
>
> Kind regards,
> Ngoc Ha Nguyen, on behalf of Team T243
> QUT IFB398 Capstone Project

### B5. Other Partner communication evidence

| Evidence | Location |
|---|---|
| First Partner meeting summary | [IFB398_T243_Partner_Meeting_1_Summary.docx](IFB398_T243_Partner_Meeting_1_Summary.docx) |
| Recording or transcript of the first Partner meeting | [link] |
| Team meeting notes from tutorials | [link to NOTE document] |
| Partner Q&A document | [link] |
| Fijian Drua opposition preview, as provided by the Partner | [link, shared within the Team only if the Partner permits] |
| Data validation results that informed the follow-up questions | `validation_results.md` |
