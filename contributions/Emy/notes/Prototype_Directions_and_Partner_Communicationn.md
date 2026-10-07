# Possible Prototype Directions and Partner Communication Evidence

**Project:** P631 Accelerating Opposition Analysis in Professional Rugby
**Team:** T243
**Author:** Ngoc Ha Nguyen (n12248746)
**Weeks covered:** 7 to 11

> Emails were exchanged through the Team's QUT email accounts and are kept in those mailboxes. Partner-owned materials, such as the shared Q&A document and the Fijian Drua preview, are held by the Team and are not published in this public repository.

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
| Weeks 6 to 7 | Email (Team to Partner) | Introduced Team T243, confirmed interest in P631 and proposed meeting times, following the Tutor's Week 5 advice | Team QUT mailbox. Advice in [Tutor Meeting Week 5 Notes](#c1-tutor-meeting-week-5-notes) |
| Weeks 6 to 7 | Email | First meeting confirmed for Friday 4 September | Team QUT mailbox |
| Before 4 September | Prepared questions | Questions on workflow, data, tools, pain points and expectations (Section B3) | Section B3 |
| Friday 4 September 2026 | First Partner meeting | Discussion with Dimitri and Jack about current workflows and pain points (Section B2) | [Partner Meeting 1 Summary](IFB398_T243_Partner_Meeting_1_Summary.docx) |
| Weeks 8 to 9 | Email (Team to Partner) | Follow-up requesting the sample CSV files and existing notebooks discussed at the meeting | Team QUT mailbox |
| Week 9 | Tutor meeting | Tutor advised continuing to follow up with the Partner, including by phone, and reporting contact attempts if there was no response | [Tutor Meeting Week 9 Notes](#c2-tutor-meeting-week-9-notes) |
| Week 9 | Open questions | Questions still to be answered once the Partner's files arrive | [Open Questions](../../Nao/reports/Open%20questions.docx) |
| Weeks 9 to 11 | Partner response | Representative event dataset (Reds versus Waratahs), a shared Q&A document and the Fijian Drua opposition preview were provided | Held by the Team. Not published because they are Partner materials |
| Week 11 | Email draft (Team to Partner) | Clarification questions from data validation (Section B4) | Section B4. To be sent after Team review |

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

This list summarises the question themes recorded in our Week 7 report, together with the general questions the Tutor recommended in Week 5 ([Tutor Meeting Week 5 Notes](#c1-tutor-meeting-week-5-notes)). The questions were grouped by theme so that the meeting could move from the current process to expectations.

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
11. Is this a new project, or does it continue work from a previous Capstone team? If so, where can we access that work?
12. Should we create our own Git repository or use yours?
13. Will we use our own equipment or equipment provided by QUT or the Partner?
14. How would you prefer to communicate with the Team, and how often?

After the meeting, the questions that remained open were recorded by Nao in [Open Questions](../../Nao/reports/Open%20questions.docx).

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
| Recording and transcript of the first Partner meeting | Prepared by Star from the meeting recording and held by the Team. Not published because it contains the Partner's own words. The content is captured in the meeting summary above |
| Tutor meeting notes | [Tutor Meeting Week 5 Notes](#c1-tutor-meeting-week-5-notes), [Tutor Meeting Week 9 Notes](#c2-tutor-meeting-week-9-notes) |
| Open questions after the first Partner meeting | [Open Questions](../../Nao/reports/Open%20questions.docx) |
| Partner Q&A document | Held by the Team. Not published because it is a Partner document |
| Fijian Drua opposition preview, as provided by the Partner | Held by the Team. Not published because it is the Partner's internal analysis. Reviewed in [Data Understanding and Validation](Data_Understanding_and_Validation.md), Section 5.2 |
| Data validation results that informed the follow-up questions | [validation_results.md](validation_results.md) |

## Part C. Tutor Meeting Notes

These notes record the Tutor's advice on Partner communication, evidence and the prototype. They are referenced in Sections B1, B3 and B5.

### C1. Tutor Meeting Week 5 Notes

**Participants:** Tutor and Team T243  
**Main topic:** Industry Partner preparation, first client meeting, and IFB398 Phase 1

---

#### 1. Industry Partner Introduction and Photos

**Tutor:**  
Have you guys got your Intro to Industry Partner approved yet?

**Student 1:**  
Not yet. I have submitted it a few times.

**Tutor:**  
Okay, let me quickly have a look at your Intro to Industry Partner and see what the issue is.

It looks like the only issue is the photos.

There are a couple of options. The quickest way is to have a photo shoot after class. Find a white wall, stand in front of it, take a number of photos, and choose the ones that fit the template best.

Once you have the photos, you can make any small touch-ups you need before putting them into the document so that they look professional.

Get that done as soon as possible. Once the photo issue is resolved, David will probably approve the document and you can move forward with contacting your client.

There is some urgency with this.

---

#### 2. What Happens After the Introduction Is Approved

**Tutor:**  
You guys have already done a lot of good research in preparation for your client.

Learning the rugby rules is actually quite important for this project because it will help you understand what your Industry Partner is talking about.

Once you update the Intro to Industry Partner, David will probably approve it quite quickly because the photos seem to be the only thing holding you up.

After that, he will send a provisional email to the client letting them know that your team will probably be working with them.

You will also receive your **IP agreements** at that point.

Make sure you check your email and sign the IP agreement as soon as possible.

The faster you complete that, the faster you can move on to contacting your client.

After that, you should receive another email telling you:

**“You are okay to contact the client now.”**

If you already have your first email prepared, you can send it immediately and start organising your first meeting.

---

#### 3. First Email to the Industry Partner

**Tutor:**  
Have you thought about what you're going to write to your client in your first email?

**Student 3:**  
We haven't thought about that yet.

**Tutor:**  
My recommendation is to say something like:

“Hi, we're Team 243. We're excited to have the opportunity to work with you.”

Then give them the **days and times your team is available**.

That allows the client to look at your availability and choose a suitable time.

After that, say:

“If these days and times don't work for you, could you please provide some days and times that you're available?”

Doing this will save you from sending many emails back and forth.

You should also ask:

**“What mode of meeting do you prefer? Would you like to meet in person on campus, or would you prefer Zoom?”**

Hopefully, they will reply with a suitable date and then you can organise your first client meeting.

I also recommend **re-attaching your Intro to Industry Partner document** to your first email.

Remember, your Industry Partner may be a QUT professor who receives around 100 emails a day.

Attaching the document again makes it easy for them to remember who your team is.

---

#### 4. What the Team Should Do Now

**Tutor:**  
Once you're finished here:

1. Take the new photos.
    
2. Upload them into the Intro to Industry Partner document.
    
3. Submit the document to Canvas again so David can review it.
    
4. Prepare your first email to the client so it is ready to send.
    

That is probably the fastest way to organise your first client meeting.

After that, you need to prepare a **list of questions for your Industry Partner** based on the project brief.

The project brief only gives you a general description of the project.

You don't know what you don't know.

You will learn much more during your first Industry Partner meeting.

So think carefully about what you want to ask before the meeting so that your team is organised and prepared.

---

#### 5. Questions to Ask the Industry Partner

**Tutor:**  
Some general questions you could ask include:

**“Do you want us to create our own Git repository, or should we use yours?”**

You should also ask:

**“Is this a new project, or are we continuing a project from a previous Capstone team?”**

Some Capstone projects continue development across several semesters.

If it is a continuation project, ask:

**“Where can we access the work completed by the previous team?”**

and

**“What are your expectations for us moving forward?”**

---

#### 6. Information to Gather During the First Meeting

**Student 4:**  
What information should we make sure to gather from the Industry Partner during our first meeting?

**Tutor:**  
It will depend on the Industry Partner and the project.

First, you need to understand **where the project currently stands**.

Ask:

- Is this a new project?
    
- Is this a continuation of an existing project?
    
- How does the Industry Partner want the team to work?
    
- What technologies do they want you to use?
    
- How will you access those technologies?
    

You should also identify what platform the project will use.

For example:

- Is it an Android project?
    
- Is it an iOS project?
    
- Is it Windows-based?
    
- What software or tools will be required?
    

HiQ has a list of software that students can access.

If you need **Microsoft Azure or Entra ID**, you can also get access through a free Microsoft student account.

You should check with the client about what they expect you to use.

---

#### 7. Equipment and Resources

**Tutor:**  
You should also ask your Industry Partner about equipment.

At the moment, HiQ does not have additional devices available for students to borrow.

However, because your project has a QUT sponsor, your Industry Partner may have access to equipment that students normally cannot access.

So ask Dmitri whether he expects you to use:

- QUT equipment, or
    
- your own equipment.
    

These are the kinds of things you will find out during the first client meeting.

---

#### 8. Research About the Industry Partner

**Tutor:**  
I would recommend looking up **Dmitri Perrin** from QUT.

See whether he has published any papers related to rugby.

If he has, read them.

There is a good chance that he has published work in this area, and reading it may help you understand the project and the context better.

I'm giving you these suggestions so that you have useful things to work on while waiting to contact the client.

---

#### 9. What the Team Should Understand Before the Next Tutor Meeting

**Tutor:**  
By our next meeting, you should be able to identify your **stakeholders** fairly easily.

You may also have a better understanding of the **workflow** that the Industry Partner expects from you.

I would aim to demonstrate that you understand:

- what the project is,
    
- who the stakeholders are,
    
- how the project may work,
    
- and what potential risks the project may have.
    

You may be able to start identifying risks once you understand the project and stakeholders better.

---

#### 10. Phase 1 Scope

**Tutor:**  
For your **Phase 1 scope**, you should probably start narrowing it down by around **Week 8**.

You need to decide what part of your artifact or prototype you are going to produce by the end of the semester.

Remember that at the end of IFB398, we only expect you to have **part of your project working**.

We do not expect you to have a complete prototype of the entire project.

What we want is a prototype that demonstrates that your team is capable of building the project.

Phase 1 is mainly:

- research,
    
- planning,
    
- and developing a small working part of the project.
    

Phase 2, or IFB399, will be much more focused on full development.

At the end of this semester, you will also create a **sprint plan** for the next phase.

However, you are not permanently locked into that sprint plan.

It can change during IFB399.

---

#### 11. IFB398 Assessment

**Student 1:**  
I have a question about the grade.

In Canvas, I can see Process 1.1 to 1.5, which together count for 20% of the semester.

Where does the other 80% come from?

**Tutor:**  
The other 80% comes from your final assessments.

You will have a **12-minute presentation**.

It will probably be a Zoom presentation where all team members present to me and David.

Your other assessment will be a **paper/report**.

That is where the remaining marks come from.

**Student 4:**  
For the presentation, are we mainly presenting what we did and explaining our process?

**Tutor:**  
Yes.

You will create a slideshow and talk about:

- your planning,
    
- the work you have completed,
    
- and where you plan to take the project in IFB399.
    

We will discuss the presentation in more detail closer to the due date.

---

#### 12. Coding During Phase 1

**Student 1:**  
What if the client asks us to implement something this semester?

I saw some students last semester doing coding during Phase 1.

**Tutor:**  
Yes, that happens.

Most likely, you will do some coding this semester.

You need to work towards something because you have to demonstrate **a portion of your artifact** before you can progress to the next phase.

You will also need to talk to your client about whether they want you to:

- work in their Git repository, or
    
- create your own Git repository.
    

Most of this semester will focus on planning.

For example, you may work on:

- user stories,
    
- wireframes,
    
- research,
    
- requirements,
    
- planning,
    

and then move into coding.

By the end of the semester, you need to demonstrate that you can build at least part of the artifact.

---

#### 13. Following Up With the Client

**Tutor:**  
If you send an email to your client and **do not hear back within 48 hours**, send another email.

They may simply have missed the first one.

It is not rude to follow up.

You are just reminding them.

**Student 1:**  
Most of our other questions are technical questions.

**Tutor:**  
That's good.

Put those technical questions on your list of questions to ask during your first Industry Partner meeting.

Alright, awesome.

You guys are free to go.

Good luck getting your first meeting with your client!

---

### C2. Tutor Meeting Week 9 Notes

**Participants:** Tutor (Sarah Mitchell) and Team T243
**Main topics:** Partner communication while waiting for data, end-of-semester prototype, and fortnightly documentation

> This is a summary prepared from the meeting recording. The full transcript is held by the Team.

---

#### 1. Partner communication

- The Team confirmed that it has already had its first meeting with the Partner. The Tutor noted that some other teams had attended a separate all-cohort session.
- From that meeting, the Team understood that the Partner's current system uses Python and that Python is recommended.
- The Team explained the current workflow. Data from an opponent's recent matches is analysed each week and the insights are given to the coaches. The pain point is that this analysis process is repeated every week and takes time, so the aim is to automate it.
- The sample data and notebooks had not yet been received.

**Tutor advice**

- Continue following up with the Partner, including by phone.
- If there is no response within about a week, email the Tutor with evidence of the contact attempts, including the dates and times of calls, so that the teaching team can follow up.
- Waiting on a client is common in Capstone. What matters is that the Team keeps making progress and shows initiative.

---

#### 2. Prototype for the end of semester

- A Team member demonstrated an early prototype. Users upload a CSV file of match events, choose a match and an analysis area such as kicking or turnovers, and the results are shown on a pitch map.
- The Tutor confirmed that this is the right basis for the end-of-semester prototype. It is locally hosted, has filters and covers different play types.
- Suggested extension: animate events on the pitch so that a match can be played through and positions viewed over time.
- Until Partner data arrives, the Team can use public or generated placeholder data and replace it with the Partner's CSV files later.
- If Partner information arrives late, the Team should present based on its current understanding with a draft sprint plan, then explain in the final report how the plan changed after receiving new information.

---

#### 3. Final assessments

- Read the final assessment requirements on Canvas and plan the remaining work backwards from them.
- The presentation can include an embedded screen-recorded demo of the prototype with live narration.
- The final report follows a similar structure to the fortnightly reports, so detailed fortnightly documentation makes the final report easier.

---

#### 4. Documentation and evidence

- In the group section, describe the shared work and link to it.
- In each individual section, link to that member's own folder and explain what was done, why, and the thinking behind it.
- Tutors have limited time per team, so evidence should be easy to find and clearly linked.
- Suggested additional planning evidence includes user stories, wireframes, a MoSCoW scope document, a team contingency plan covering absences and backup roles, and ethical considerations such as data storage and anonymity.
