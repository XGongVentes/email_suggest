<html>
<head>
	<style>
		.left_panel {
			width: 57%;
			height: 560px;
			float: left;
			overflow-y: scroll;
		}
		.right_panel {
			width: 40%;
			height: 373px;
			padding-right:0.5cm;
			float: right;
			overflow-y: scroll;
		}
		input {
			line-height: 20px;
		}
		input[type=submit] {
 		   width: 3cm;  
 		   height: 20px;
 		   font-size: 1.8cm;
		}
		.header {
			margin-top: 0.5cm;
			margin-bottom: 0.2cm;
		}
		.ttttable {
    		table-layout:fixed;
		}
		table {
			table-layout:fixed;
                        border-collapse: collapse;
		}
		th {
			padding-left:0.2cm;
			text-align: left;
			width: 3cm;
		}
		th, td {
			padding-left: 0.2cm;
			padding-top: 0.cm;
			padding-bottom: 0.cm;
			overflow: hidden;
			text-overflow: ellipsis;
			white-space: nowrap;
		}
                .verify_btn  {
                        padding-right: 0.1cm;
                        text-align: right;
               }
		.deco tr:nth-child(even) {
			background: #DDD
		}
		.deco tr:nth-child(odd) {
			background: #EEE
		}
                .sep_row {
                    height: 0px
                }
	</style>
</head>
<body>
<div class="header"><h3> Generate suggested emails: </h3></div>
<form action = "http://13.76.171.208:8080/email_suggest" method="post">
    <table>
        <tr><td> contact name: </td>
            <td> email domain: </td>
            <td></td><td>company name:</td><td></td></tr>
        <tr class="sep_row"><td colspan=5> </td></tr>
        <tr><td> <input type="text" name="name" size=40 value="{{name}}"> </td>
            <td> @<input type="text" name="domain" size=40 value="{{domain}}"> </td>
            <td> or </td>
            <td> <input type="text" name="company_name" size=60 disabled value="not implemented"> </td>
            <td> <input type="submit" name="suggest" value="Suggest"> </td></tr>
    </table>
</form>

<hr>

% if stage == 0:
	<h4></h4>
% else:
	<h4>results:</h4>
	% suggested_emails = suggests
        % firstname = nname['firstname2'].title() if nname.get('firstname2') else ''
        % christian = nname['firstname1'].title() if nname.get('firstname1') else ''
        % lastname = nname['lastname'].title() if nname.get('lastname') else ''	
        % if christian and not firstname:
        %     firstname = christian
        %     christian = ''
        % end
	<div class="left_panel">
            <table border = 0  width=100%>
            <tr> <td> name parsing result</td>
                 <td padding=0>Given Name</td>  <td>Family Name</td>  <td>Christian Name</td></tr>
            <tr class="sep_row"> <td colspan=4><hr></td> </tr>
            <tr> <td></td> <td>{{firstname}}</td> <td>{{lastname}}</td> <td>{{christian}}</td> </tr>
            <tr class = "sep_row"> <td colspan=4><hr></td></tr>
            % if total < 1:
                <tr><td> {{domain}}:</td><td>No training email address </td></tr></table>
            % else:
                <tr><td colspan=4> Suggested emails (Training set size: {{total}}) </td></tr>
                <tr class = "sep_row"><td><hr></td></tr></table>  
                <table border = 1>
                % rank = 0
                <form action="http://13.76.171.208:8080/email_suggest" method="post">
                % for prob, pattern, emails in suggested_emails:
		    <tr><td width="35%"><span style="font-size:95%">{{prob}} => {{pattern}}</span></td>
                        <td width="65%">
                          <table width=100% border=0>
                    % for email in emails:
                              % rank += 1
                              <tr><td width=65%>{{email}}</td>
                              % vcode = vcodes[rank-1]
                              % if vcode is not None:
                                 %      status = 'Success' if vcode==1 else 'Fail' if vcode==0 else 'Timeout' if vcode==-1 else 'Unknown' 
                                        <td class="verify_btn">{{status}}</td></tr>
                              % else:
                                    <td class="verify_btn">
                                       <input style="width:1cm" type="submit" name="known_{{rank}}_{{email}}" value="yes">
                                       <input style="width:1cm" type="submit" name="false_{{rank}}_{{email}}" value="no">
                                       <input style="width:1.5cm" type="submit" name="verify_{{rank}}_{{email}}" value="verify">
                                    </td></tr>
                              % end
                    % end
                    </table>
                    </td>
                    </tr>
                % end
                </form>
            % end
%end
 </table></div>
	<div class="right_panel">
	<table border=0 width=100%>
                % vnum = test_stats['vnum']
                % accurate = test_stats['accurate']
                % score = test_stats['score']
		<tr><td>Test results</td> <td> tested num. = {{vnum}}</td> <td> accurate = {{accurate}}</td> <td> score = {{score}}</td></tr>
                <tr><td class="sep_row" colspan=4><hr></td></tr>
         </table>
         <table width=100% border=0>
		<tr><td width=75%>email address</td>
                <td width =15% align="right"> verified </td> 
		<td width=10% align="right">  rank </td></tr>
                <tr><td class="sep_row" colspan=3><hr></td></tr>
                % if 'cemail' in verification:
                %    cemail = verification['cemail']
                %    verified = 'True' if test_results[cemail][0]==1 else 'False' if test_results[cemail][0]==0 else 'Unknown'
                %    rank = test_results[cemail][1]
                     <tr bgcolor="#EEEEEE"><td>{{cemail}}</td><td align="right">{{verified}}</td><td align="right">{{rank}}</td></tr>
                     <tr><td class="sep_row" colspan=3><hr></td></tr>
                % end
                % if test_results:
                    % for vemail, value in sorted(test_results.items(), key=lambda x: x[1][2], reverse=True):
                    %    verified = 'True' if value[0]==1 else 'False' if value[0] ==0 else 'Unknown'
                    %    rank = value[1] 
                        <tr><td>{{vemail}}</td>
                        <td align="right">{{verified}}</td>
                        <td align="right">{{rank}}</td></tr>
                    % end
                % end
		</table></div>
</body>
</html>
